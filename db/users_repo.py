# backend/db/users_repo.py
"""
Data access for users.
"""
from typing import Dict, Any, Optional
from bson.objectid import ObjectId
from db.client import users_collection, _ensure_collection

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
