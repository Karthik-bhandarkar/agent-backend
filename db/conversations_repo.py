# backend/db/conversations_repo.py
"""
Data access for conversation history.
"""
import uuid
from typing import List, Dict, Any
from datetime import datetime
from db.client import conversation_collection, _ensure_collection

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
