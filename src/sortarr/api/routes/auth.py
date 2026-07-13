"""sortarr.api.routes.auth — OAuth authentication routes."""

import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from sortarr.core.auth import OAuthManager

log = logging.getLogger("sortarr.api.routes.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


# Response models
class AuthStatusResponse(BaseModel):
    """OAuth authentication status."""

    authenticated: bool
    expires_at: str | None = None


class LogoutResponse(BaseModel):
    """Logout confirmation."""

    message: str


# Helper to get OAuthManager from request
def _get_oauth_manager(request: Request) -> OAuthManager:
    """Get OAuthManager from app state.

    Raises HTTPException 503 if OAuth is not configured.
    """
    state = request.app.state.sortarr
    if not hasattr(state, "oauth_manager") or state.oauth_manager is None:
        raise HTTPException(
            status_code=503,
            detail="OAuth not configured — set SORTARR_CLIENT_SECRET_PATH and SORTARR_PUBLIC_URL",
        )
    return state.oauth_manager


@router.get("/login", response_class=RedirectResponse)
async def login(request: Request):
    """Redirect to Google OAuth consent screen.

    Returns 302 redirect to Google authorization URL.
    Raises 503 if client_secret.json is missing.
    """
    oauth = _get_oauth_manager(request)
    try:
        auth_url = oauth.get_authorization_url()
        log.info("redirecting to OAuth consent screen")
        return RedirectResponse(url=auth_url, status_code=302)
    except FileNotFoundError as e:
        log.error("OAuth client secret file missing: %s", e)
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e


@router.get("/callback")
async def callback(
    request: Request,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="OAuth state parameter for CSRF protection"),
):
    """Handle OAuth callback and exchange code for tokens.

    Verifies the state parameter to prevent CSRF attacks.
    Saves credentials to database.
    Returns success message.
    Raises 503 if client_secret.json is missing.
    Raises 400 if state verification fails.
    """
    oauth = _get_oauth_manager(request)

    if not code:
        raise HTTPException(status_code=400, detail="missing authorization code")

    try:
        oauth.handle_callback(code, state)
        log.info("OAuth callback successful — credentials saved")
        return {"message": "authentication successful", "authenticated": True}
    except ValueError as e:
        # State verification failed
        log.error("OAuth state verification failed: %s", e)
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e
    except FileNotFoundError as e:
        log.error("OAuth client secret file missing: %s", e)
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e
    except Exception as e:
        log.error("OAuth callback failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"authentication failed: {e}"
        ) from e


@router.get("/status", response_model=AuthStatusResponse)
async def status(request: Request):
    """Check authentication status.

    Returns whether user is authenticated and token expiry.
    """
    oauth = _get_oauth_manager(request)
    authenticated = oauth.is_authenticated()

    # Get expiry if authenticated
    expires_at = None
    if authenticated:
        credentials = oauth.get_credentials()
        if credentials and credentials.expiry:
            expires_at = credentials.expiry.isoformat()

    return AuthStatusResponse(authenticated=authenticated, expires_at=expires_at)


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request):
    """Clear stored credentials.

    Returns confirmation message.
    """
    oauth = _get_oauth_manager(request)
    oauth.clear_credentials()
    log.info("user logged out — credentials cleared")
    return LogoutResponse(message="logged out successfully")
