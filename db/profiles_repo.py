# backend/db/profiles_repo.py
"""
Data access for profiles.
"""
from typing import Dict, Any
from db.client import profiles_collection, _ensure_collection
from db.users_repo import update_user_profile_complete

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
