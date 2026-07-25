# backend/routers/history.py
"""
Conversation history routes.

Endpoints to fetch and delete stored conversation turns for a user.
"""
from fastapi import APIRouter
from fastapi import APIRouter, HTTPException
from db.conversations_repo import get_conversation_history, delete_conversation_turn

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/{user_id}")
def fetch_history(user_id: str):
    """
    Return the conversation history for a given user.

    Route: GET /history/{user_id}
    
    Args:
        user_id: The unique identifier for the user (path parameter).

    Returns:
        dict: A dictionary containing `user_id`, a `turns` array, and `total_turns`.
    """
    turns = get_conversation_history(user_id)
    return {
        "user_id": user_id,
        "turns": turns,
        "total_turns": len(turns),
    }

@router.delete("/{user_id}/{turn_id}")
def delete_turn(user_id: str, turn_id: str):
    """
    Delete a specific conversation turn by its ID.

    Route: DELETE /history/{user_id}/{turn_id}

    Args:
        user_id: The unique identifier for the user (path parameter).
        turn_id: The unique identifier for the specific conversation turn (path parameter).

    Returns:
        dict: A success status dictionary containing the deleted `turn_id`.

    Raises:
        HTTPException(404): if the turn is not found or deletion fails.
    """
    success = delete_conversation_turn(user_id, turn_id)
    if not success:
        raise HTTPException(status_code=404, detail="Turn not found or not deleted")
    return {"status": "deleted", "turn_id": turn_id}
