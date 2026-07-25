# backend/utils/password_hash.py
"""
Password hashing and verification utilities.

Wraps passlib's pbkdf2_sha256 scheme to securely hash passwords for storage
and verify plaintext passwords during login.
"""
from passlib.context import CryptContext

# Configure the hashing context to use pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

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
