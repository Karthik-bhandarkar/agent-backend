# backend/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# UPDATE THIS CLASS - Add profile_complete field
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    profile_complete: bool  # ← ADD THIS LINE
    message: Optional[str] = None