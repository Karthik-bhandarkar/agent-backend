from pydantic import BaseModel

class MessageHistory(BaseModel):
    user_id: int
    message: str
    response: str
