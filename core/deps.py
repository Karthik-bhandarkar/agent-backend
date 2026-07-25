# backend/core/deps.py
"""
FastAPI Dependencies for route protection and user injection.
"""
from fastapi import Request, HTTPException, status
from core.security import verify_jwt_token

def get_current_user(request: Request) -> str:
    """
    Dependency to extract and verify the JWT token from the Authorization header.
    
    Args:
        request: The incoming FastAPI request.
        
    Returns:
        str: The decoded user_id from the valid JWT token.
        
    Raises:
        HTTPException(401): If the Authorization header is missing, malformed, 
                            or if the token is invalid/expired.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header (expected 'Bearer <token>')"
        )
    
    # Extract the token string after 'Bearer '
    token = auth_header.split(" ")[1]
    
    # Verify using our core security utility
    payload = verify_jwt_token(token)
    
    # payload is None if expired or invalid
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
        
    return payload["user_id"]
