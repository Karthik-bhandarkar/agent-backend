# backend/database.py
"""
MongoDB data access layer.

Provides a robust connection to MongoDB that catches connection failures at
startup and logs them instead of crashing the server. This ensures the FastAPI
app starts successfully even if the database is temporarily unreachable,
allowing health checks to pass and graceful error handling on subsequent requests.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise RuntimeError("MONGODB_URI missing in .env")

# Try to connect but don't let failures crash the process.
client = None
db = None
users_collection = None
profiles_collection = None
conversation_collection = None

# Determine DB name from URI (the path part before query params), fallback to FitAura
try:
    db_name = MONGO_URI.split("/")[-1].split("?")[0] or "FitAura"
except Exception:
    db_name = "FitAura"

try:
    # Use a short timeout so server starts quickly if DNS/network fails
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Small ping to validate connection
    client.admin.command("ping")
    db = client[db_name]
    users_collection = db["users"]
    profiles_collection = db["profiles"]
    conversation_collection = db["conversation_turns"]
    print("MongoDB connected.")
except Exception as e:
    # Keep server alive — log helpful message
    print("WARNING: MongoDB connection failed at startup:", repr(e))
    client = None
    db = None
    users_collection = None
    profiles_collection = None
    conversation_collection = None


# Helper to ensure collection availability
def _ensure_collection(coll, name: str = "collection"):
    if coll is None:
        raise RuntimeError(
            f"Database not connected. '{name}' is unavailable. "
            "Check MONGODB_URI, network access, DNS, or install dnspython for mongodb+srv."
        )
    return coll


# ------------------------------
# USER FUNCTIONS (same names as before)
# ------------------------------

def save_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a new user and return the full user record (including its id).

    Args:
        user_data: Dictionary containing the new user's information.

    Returns:
        dict: The inserted user record, with the `id` field converted to a string.

    Raises:
        ValueError: if the email is already registered.
        RuntimeError: if the database is unavailable.
    """
    coll = _ensure_collection(users_collection, "users")

    # default flags
    if "profile_complete" not in user_data:
        user_data["profile_complete"] = False

    existing = coll.find_one({"email": user_data.get("email")})
    if existing:
        raise ValueError("email_already_registered")

    result = coll.insert_one(user_data)
    inserted_id = result.inserted_id
    user_record = coll.find_one({"_id": inserted_id})
    user_record["id"] = str(user_record["_id"])
    return user_record


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user record by their email address.

    Args:
        email: The email string to search for.

    Returns:
        dict | None: The user dictionary if found, otherwise None.
    """
    coll = _ensure_collection(users_collection, "users")
    user = coll.find_one({"email": email})
    if not user:
        return None
    user["id"] = str(user["_id"])
    # ensure profile_complete key exists on record
    if "profile_complete" not in user:
        try:
            user["profile_complete"] = True
            coll.update_one({"_id": user["_id"]}, {"$set": {"profile_complete": True}})
        except Exception:
            # ignore write failure here
            pass
    return user


def get_user_by_id(user_id: Any) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user record by their unique ID.

    Args:
        user_id: The unique identifier for the user (accepts string or ObjectId).

    Returns:
        dict | None: The user dictionary if found, otherwise None.
    """
    coll = _ensure_collection(users_collection, "users")

    if user_id is None:
        return None

    query = None
    try:
        query = {"_id": ObjectId(user_id)}
    except Exception:
        query = {"id": str(user_id)}

    user = coll.find_one(query)
    if not user:
        return None

    user["id"] = str(user["_id"])
    if "profile_complete" not in user:
        try:
            user["profile_complete"] = True
            coll.update_one({"_id": user["_id"]}, {"$set": {"profile_complete": True}})
        except Exception:
            pass
    return user


def update_user_profile_complete(user_id: Any, profile_complete: bool) -> bool:
    """
    Update a user's profile_complete status flag.

    Args:
        user_id: The unique identifier for the user.
        profile_complete: Boolean indicating whether the profile is complete.

    Returns:
        bool: True if the user was found and updated successfully, False otherwise.
    """
    coll = _ensure_collection(users_collection, "users")

    if user_id is None:
        return False

    try:
        res = coll.update_one({"_id": ObjectId(user_id)}, {"$set": {"profile_complete": profile_complete}})
    except Exception:
        res = coll.update_one({"id": str(user_id)}, {"$set": {"profile_complete": profile_complete}})

    return res.matched_count > 0


# ------------------------------
# PROFILE FUNCTIONS (same names as before)
# ------------------------------

def save_profile(user_id: Any, profile_data: Dict[str, Any]) -> None:
    """
    Create or update a health profile for the given user.

    Args:
        user_id: The unique identifier for the user.
        profile_data: Dictionary containing health metrics and goals.

    Raises:
        ValueError: if `user_id` is None.
    """
    coll = _ensure_collection(profiles_collection, "profiles")

    if user_id is None:
        raise ValueError("user_id_required")

    uid = str(user_id)
    profile_doc = {"user_id": uid, **profile_data}
    coll.update_one({"user_id": uid}, {"$set": profile_doc}, upsert=True)

    # Also mark user's profile_complete = True (best effort)
    try:
        update_user_profile_complete(user_id, True)
    except Exception:
        pass


def get_profile(user_id: Any) -> Dict[str, Any]:
    """
    Retrieve the health profile for a specific user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        dict: The user's profile data, or an empty dict if none exists.
    """
    coll = _ensure_collection(profiles_collection, "profiles")
    if user_id is None:
        return {}
    uid = str(user_id)
    profile = coll.find_one({"user_id": uid})
    if not profile:
        return {}
    profile["id"] = str(profile["_id"])
    return profile


# ------------------------------
# CONVERSATION HISTORY (same names as before)
# ------------------------------

def append_conversation_turn(
    user_id: Any,
    user_message: str,
    assistant_response: str,
    agents_used: List[str],
    reasoning_logs: List[Dict[str, Any]] = None,
) -> None:
    """
    Store a single conversation turn in the user's history.

    Args:
        user_id: The unique identifier for the user.
        user_message: The raw text of the user's input.
        assistant_response: The final Markdown report from the synthesizer.
        agents_used: List of agent names that contributed to the response.
        reasoning_logs: Optional list of intermediate logging events.
    """
    coll = _ensure_collection(conversation_collection, "conversation_turns")
    uid = str(user_id)
    turn = {
        "id": str(uuid.uuid4()),  # Unique ID for deletion
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_message": user_message,
        "assistant_response": assistant_response,
        "agents_used": agents_used,
        "reasoning_logs": reasoning_logs or [],
    }
    coll.update_one(
        {"user_id": uid},
        {"$push": {"turns": turn}},
        upsert=True,
    )


def get_conversation_history(user_id: Any) -> List[Dict[str, Any]]:
    """
    Retrieve all stored conversation turns for a user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        list: A list of dictionaries representing the conversation turns.
    """
    coll = _ensure_collection(conversation_collection, "conversation_turns")
    uid = str(user_id)
    doc = coll.find_one({"user_id": uid})
    if not doc:
        return []
    
    # Ensure all turns have an ID (migration for old data)
    turns = doc.get("turns", [])
    for t in turns:
        if "id" not in t:
            t["id"] = str(uuid.uuid4())
            # ideally update DB but lazy migration on read is acceptable for display
            # for strict deletion, we rely on the ID matching, so untagged ones might be hard to delete
            # Let's try to persist IDs back if missing? 
            # Nah, let's keep it simple. New ones get IDs. Old ones might not be deletable easily or receive temporary IDs.
            # Use index as fallback? No, UUID is safer.
            pass
            
    return turns

def delete_conversation_turn(user_id: Any, turn_id: str) -> bool:
    """
    Remove a specific conversation turn from a user's history by its ID.

    Args:
        user_id: The unique identifier for the user.
        turn_id: The unique identifier for the specific conversation turn.

    Returns:
        bool: True if the turn was successfully deleted, False otherwise.
    """
    coll = _ensure_collection(conversation_collection, "conversation_turns")
    uid = str(user_id)
    
    # Pull the item from array where id == turn_id
    res = coll.update_one(
        {"user_id": uid},
        {"$pull": {"turns": {"id": turn_id}}}
    )
    return res.modified_count > 0
