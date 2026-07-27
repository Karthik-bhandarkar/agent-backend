"""
Google OAuth2 authentication routes.

Handles the login redirect and the callback that exchanges the code for a token,
creating or finding the user, and finally redirecting back to the frontend.
"""
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import os
import requests

from db.users_repo import get_user_by_email, save_user
from core.security import hash_password, create_jwt_token
from core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["google-auth"])


@router.get("/auth/google/login")
def google_login():
    """
    Step 1: Send user to Google sign-in page.

    Route: GET /auth/google/login

    Returns:
        RedirectResponse: Redirects the user to the Google OAuth2 consent screen
        with 'select_account' prompt so users can choose from multiple Google accounts.

    Raises:
        HTTPException(500): if Google OAuth environment variables are missing.
    """
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    # Debug logs for deployment troubleshooting
    logger.info("Google Login initiated.")
    logger.info(f"Client ID configured: {bool(GOOGLE_CLIENT_ID)}")
    logger.info(f"Redirect URI configured: {bool(GOOGLE_REDIRECT_URI)}")
    if GOOGLE_REDIRECT_URI:
        logger.info(f"Redirect URI value: {GOOGLE_REDIRECT_URI}")

    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured on the server (Missing Env Vars: GOOGLE_CLIENT_ID or GOOGLE_REDIRECT_URI)"
        )

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",  # Always show account picker — supports multiple Google accounts
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/auth/google/callback")
def google_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    """
    Step 2: Handle the Google OAuth callback, get user info, and redirect to frontend.

    Route: GET /auth/google/callback

    Args:
        request: The raw FastAPI request.
        code: The authorization code returned by Google.
        error: Any error string returned by Google (e.g. 'access_denied' if user cancelled).

    Returns:
        RedirectResponse: Redirects to the frontend /google-callback URL with JWT token
        and user info, or redirects to /login with a descriptive error param on failure.
    """
    # CRITICAL: Must be the deployed Netlify frontend URL in production
    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    logger.info(f"Google callback received. error={error}, code_present={bool(code)}")
    logger.info(f"Frontend redirect target: {FRONTEND_BASE_URL}")

    # Handle errors returned by Google (e.g., user clicked "Cancel")
    if error:
        logger.warning(f"Google returned OAuth error: {error}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error={error}")

    if not code:
        logger.error("Google callback received with no code and no error")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=missing_code")

    # Validate all required env vars before proceeding
    if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI]):
        logger.error("Google OAuth env vars missing on server — check Render environment settings")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=server_misconfigured")

    # --- Step A: Exchange authorization code for Google tokens ---
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            timeout=10,  # Prevent request from hanging indefinitely
        )
        token_resp.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Timeout while contacting Google token endpoint")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to exchange Google code for access token: {e}")
        # Try to log the response body for more context
        try:
            logger.error(f"Google token error response: {token_resp.text}")
        except Exception:
            pass
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=token_exchange_failed")

    token_json = token_resp.json()
    access_token = token_json.get("access_token")

    if not access_token:
        logger.error(f"No access_token in Google response: {list(token_json.keys())}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=no_access_token")

    # --- Step B: Fetch user profile from Google ---
    try:
        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        userinfo_resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch user profile from Google: {e}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=user_info_failed")

    userinfo = userinfo_resp.json()
    email = userinfo.get("email")
    name = userinfo.get("name") or userinfo.get("given_name") or "Google User"
    picture = userinfo.get("picture", "")

    if not email:
        logger.error("Google user info response missing email field — email permission not granted")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=no_email_permission")

    logger.info(f"Google user authenticated: email={email}")

    # --- Step C: Find or create user in database ---
    try:
        user = get_user_by_email(email)
        if not user:
            # New user — generate a random password (they authenticate via Google, not password)
            random_password = os.urandom(16).hex()
            user = save_user({
                "email": email,
                "name": name,
                "picture": picture,
                "password_hash": hash_password(random_password),
                "profile_complete": False,
                "auth_provider": "google",
            })
            logger.info(f"Created new user via Google OAuth: {email}")
        else:
            logger.info(f"Existing user signed in via Google OAuth: {email}")
    except Exception as e:
        logger.error(f"Database error during Google auth for {email}: {e}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=database_error")

    # --- Step D: Issue our application JWT ---
    try:
        token = create_jwt_token(str(user["id"]))
    except Exception as e:
        logger.error(f"JWT generation failed: {e}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login?google_error=token_generation_failed")

    # --- Step E: Redirect to frontend with token and user data ---
    profile_complete = bool(user.get("profile_complete", False))

    redirect_params = {
        "userId": str(user["id"]),
        "name": name,
        "email": email,
        "token": token,
        "from": "google",
        "profile_complete": "true" if profile_complete else "false",
    }

    redirect_url = f"{FRONTEND_BASE_URL}/google-callback?" + urlencode(redirect_params)
    logger.info(f"Google auth complete — redirecting to frontend. profile_complete={profile_complete}")
    return RedirectResponse(redirect_url)