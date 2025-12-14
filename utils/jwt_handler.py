# backend/utils/jwt_handler.py
import jwt
from datetime import datetime, timedelta
import os

# Read from .env file
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback-key-123")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

from typing import Any

def create_jwt_token(user_id: Any):
    """Create a JWT token for the user"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_jwt_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_jwt_token(token: str):
    """Verify if token is valid"""
    return decode_jwt_token(token)