from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import os
import requests

from database import get_user_by_email, save_user
from utils.password_hash import hash_password
# Import jwt_handler at the top level to avoid scope issues
from utils.jwt_handler import create_jwt_token

router = APIRouter(tags=["google-auth"])

@router.get("/auth/google/login")
def google_login():
    """Step 1: Send user to Google sign-in page."""
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    # Debug logs for deployment troubleshooting
    print(f"DEBUG: Starting Google Login.")
    print(f"DEBUG: Client ID configured: {bool(GOOGLE_CLIENT_ID)}")
    print(f"DEBUG: Redirect URI configured: {bool(GOOGLE_REDIRECT_URI)}")

    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=500, 
            detail="Google OAuth is not configured on the server (Missing Env Vars)"
        )

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/auth/google/callback")
def google_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    """Step 2: Google returns here. We get user info and send them back to frontend."""
    
    # CRITICAL: In production, this must be your Render Frontend URL
    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    # Handle errors returned by Google
    if error:
        print(f"ERROR: Google returned error: {error}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error={error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' in callback")

    # Exchange code for access token
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    try:
        token_resp = requests.post("https://oauth2.googleapis.com/token", data=token_data)
        token_resp.raise_for_status() # Raise exception for 4xx/5xx errors
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to exchange token: {e}")
        # Return to frontend with error
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?error=token_exchange_failed")

    token_json = token_resp.json()
    access_token = token_json.get("access_token")

    # Get Google User Profile
    userinfo_resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    if userinfo_resp.status_code != 200:
         return RedirectResponse(f"{FRONTEND_BASE_URL}/login?error=user_info_failed")

    userinfo = userinfo_resp.json()
    email = userinfo.get("email")
    name = userinfo.get("name") or "Google User"

    if not email:
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?error=no_email_permission")

    # Find or Create User in Database
    user = get_user_by_email(email)
    if not user:
        # Create new user with random password
        random_password = os.urandom(16).hex()
        user = save_user(
            {
                "email": email,
                "name": name,
                "password_hash": hash_password(random_password),
                "profile_complete": False # Explicitly mark as new
            }
        )

    # Generate JWT Token for our app
    token = create_jwt_token(str(user["id"]))

    # Redirect to Frontend with Token
    # We strip the trailing slash from FRONTEND_BASE_URL just in case
    base_url = FRONTEND_BASE_URL.rstrip("/")
    
    params = {
        "userId": str(user["id"]),
        "name": name,
        "email": email,
        "token": token,     
        "from": "google",
        "profile_complete": str(user.get("profile_complete", "False"))
    }

    redirect_url = f"{base_url}/google-callback?" + urlencode(params)
    return RedirectResponse(redirect_url)