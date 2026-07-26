# backend/core/security.py
"""
Security utilities including password hashing and JWT token handling.
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Any
from passlib.context import CryptContext

# --- JWT Configuration ---
# Accepts both JWT_SECRET_KEY and JWT_SECRET (either name works in Render)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("JWT_SECRET", "fallback-key-123")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# --- Password Hashing Configuration ---
# Configure the hashing context to use pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# --- JWT Functions ---
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

# --- Password Hashing Functions ---
def hash_password(password: str):
    """
    Securely hash a plaintext password.

    Args:
        password: The plaintext password string.

    Returns:
        str: The hashed password string.
    """
    return pwd_context.hash(password)

def verify_password(password: str, hash_val: str):
    """
    Verify a plaintext password against a stored hash.

    Args:
        password: The plaintext password entered by the user.
        hash_val: The secure hash stored in the database.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(password, hash_val)
