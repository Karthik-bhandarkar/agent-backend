from fastapi import APIRouter
from fastapi import APIRouter, HTTPException
from database import get_conversation_history, delete_conversation_turn

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/{user_id}")
def fetch_history(user_id: str):
    """
    Return the conversation history for a given user_id.
    Each item contains:
    - timestamp
    - user_message
    - assistant_response
    - agents_used
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
    Delete a specific conversation turn by ID.
    """
    success = delete_conversation_turn(user_id, turn_id)
    if not success:
        raise HTTPException(status_code=404, detail="Turn not found or not deleted")
    return {"status": "deleted", "turn_id": turn_id}
