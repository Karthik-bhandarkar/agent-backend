# backend/utils/jwt_handler.py
"""
JSON Web Token (JWT) issuing and verification utilities.

Handles the creation and validation of JWTs using a secret key and expiration
settings loaded from environment variables.
"""
import jwt
from datetime import datetime, timedelta
import os

# Read from .env file
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback-key-123")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

from typing import Any

def create_jwt_token(user_id: Any):
    """
    Issue a new JWT token for the authenticated user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        str: A signed JWT string containing the user ID and expiration timestamp.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_jwt_token(token: str):
    """
    Decode and verify a JWT token's signature and expiration.

    Args:
        token: The raw JWT string from the authorization header.

    Returns:
        dict | None: The decoded payload if valid; returns None if the token
        is expired or invalid rather than raising an exception.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_jwt_token(token: str):
    """
    Alias for decode_jwt_token to verify if a token is valid.

    Args:
        token: The raw JWT string.

    Returns:
        dict | None: The decoded payload, or None if validation fails.
    """
    return decode_jwt_token(token)