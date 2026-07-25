# backend/models/message_history.py
"""
Pydantic schemas for message history operations.

Used by the history/chat features to serialize stored conversation turns.
"""
from pydantic import BaseModel

class MessageHistory(BaseModel):
    """Schema representing an individual conversation turn, used by history endpoints."""
    user_id: int
    message: str
    response: str
