from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import os
import requests

from database import get_user_by_email, save_user
from utils.password_hash import hash_password

router = APIRouter(tags=["google-auth"])


@router.get("/auth/google/login")
def google_login():
    """Step 1: send user to Google sign-in page."""
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    print("google_login called")
    print("GOOGLE_CLIENT_ID present:", bool(GOOGLE_CLIENT_ID))
    print("GOOGLE_REDIRECT_URI present:", bool(GOOGLE_REDIRECT_URI))

    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

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

    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    if error:
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error={error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' in callback")

    # exchange code for tokens
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_resp = requests.post("https://oauth2.googleapis.com/token", data=token_data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to obtain tokens from Google")

    token_json = token_resp.json()
    access_token = token_json.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in Google response")

    # get Google profile
    userinfo_resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from Google")

    userinfo = userinfo_resp.json()
    email = userinfo.get("email")
    name = userinfo.get("name") or "Google User"

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    # find or create local user
    user = get_user_by_email(email)
    if not user:
        random_password = os.urandom(16).hex()
        user = save_user(
            {
                "email": email,
                "name": name,
                "password_hash": hash_password(random_password),
            }
        )

    # send user to frontend with data in URL
    from utils.jwt_handler import create_jwt_token

    token = create_jwt_token(user["id"])

    params = {
        "userId": user["id"],
        "name": user["name"],
        "email": user["email"],
        "token": token,     
        "from": "google",
    }

    redirect_url = f"{FRONTEND_BASE_URL}/google-callback?" + urlencode(params)
    return RedirectResponse(redirect_url)
