# backend/routers/chat.py
"""
Synchronous chat endpoint.

Receives user messages and calls the orchestrator (process_query) to generate
a response. Useful for simple REST clients that don't support WebSockets.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.orchestrator import process_query

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    """
    Process a chat message synchronously and return the assistant's response.

    Route: POST /chat

    Args:
        req: Parsed request body containing `user_id` and `message`.

    Returns:
        dict: The synthesized final `response` string and an `agents_used` list.
    """
    response, trace = process_query(req.user_id, req.message)
    return {"response": response, "agents_used": trace}
