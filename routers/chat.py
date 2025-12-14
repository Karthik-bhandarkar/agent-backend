from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.orchestrator import process_query

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    response, trace = process_query(req.user_id, req.message)
    return {"response": response, "agents_used": trace}
