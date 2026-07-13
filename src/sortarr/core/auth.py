"""
sortarr.core.auth — OAuth 2.0 credential management (DB-backed).

Stores credentials in the oauth_credentials table instead of pickle files.
Provides AuthorizedSession for API calls with auto-refresh.
"""

import json
import logging
import threading
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from sortarr.db.connection import get_connection

log = logging.getLogger("sortarr.core.auth")

# OAuth 2.0 scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


class OAuthManager:
    """Manages OAuth 2.0 credentials with database storage."""

    def __init__(self, client_secret_path: str, redirect_uri: str):
        """Initialize OAuth manager.

        client_secret_path: Path to Google OAuth client secret JSON
        redirect_uri: OAuth callback URL (e.g., "http://localhost:8080/api/auth/callback")
        """
        self.client_secret_path = client_secret_path
        self.redirect_uri = redirect_uri
        self._refresh_lock = threading.Lock()

    def get_authorization_url(self) -> str:
        """Generate OAuth 2.0 authorization URL.

        User should be redirected to this URL to grant consent.
        Stores the OAuth state and PKCE code_verifier in the database
        for later verification in the callback.

        Raises:
            FileNotFoundError: If client_secret.json does not exist
        """
        if not Path(self.client_secret_path).exists():
            raise FileNotFoundError(
                f"OAuth client secret not found at {self.client_secret_path}. "
                f"Download client_secret.json from Google Cloud Console "
                f"(APIs & Services > Credentials) and place it at this path."
            )
        flow = Flow.from_client_secrets_file(
            self.client_secret_path, scopes=SCOPES, redirect_uri=self.redirect_uri
        )
        auth_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", prompt="consent"
        )
        
        # Store state and code_verifier for callback verification
        self._save_oauth_state(state, flow.code_verifier)
        log.info("OAuth state saved to database")
        
        return auth_url

    def handle_callback(self, code: str, state: str) -> None:
        """Exchange authorization code for tokens and save to DB.

        Verifies the OAuth state parameter matches what was stored during
        authorization to prevent CSRF attacks. Restores the PKCE code_verifier
        so the token exchange succeeds.

        Args:
            code: Authorization code from OAuth callback query parameter
            state: State parameter from OAuth callback (for CSRF protection)

        Raises:
            FileNotFoundError: If client_secret.json does not exist
            ValueError: If state parameter is invalid or missing
        """
        if not Path(self.client_secret_path).exists():
            raise FileNotFoundError(
                f"OAuth client secret not found at {self.client_secret_path}. "
                f"Download client_secret.json from Google Cloud Console "
                f"(APIs & Services > Credentials) and place it at this path."
            )
        
        # Verify state and retrieve code_verifier
        code_verifier = self._verify_oauth_state(state)
        
        # Create flow and restore code_verifier for PKCE
        flow = Flow.from_client_secrets_file(
            self.client_secret_path, scopes=SCOPES, redirect_uri=self.redirect_uri
        )
        flow.code_verifier = code_verifier
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        self.save_credentials(credentials)
        log.info("OAuth credentials saved to database")

    def save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to the oauth_credentials table."""
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }
        # Filter out None values to keep JSON clean
        token_data = {k: v for k, v in token_data.items() if v is not None}
        token_json = json.dumps(token_data)

        conn = get_connection()
        conn.execute(
            """
            INSERT INTO oauth_credentials (id, token_json, created_at, updated_at)
            VALUES (1, ?, datetime('now'), datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                token_json = excluded.token_json,
                updated_at = datetime('now')
        """,
            (token_json,),
        )
        conn.commit()

    def get_credentials(self) -> Credentials | None:
        """Load credentials from the oauth_credentials table.
        
        Automatically clears credentials if scopes have changed (e.g., v1→v2 migration).
        User must re-authenticate with the new scopes.
        """
        conn = get_connection()
        row = conn.execute(
            "SELECT token_json FROM oauth_credentials WHERE id = 1"
        ).fetchone()
        if not row:
            return None

        token_data = json.loads(row["token_json"])
        stored_scopes = token_data.get("scopes")
        
        # Check if scopes have changed (e.g., v1 had 4 scopes, v2 has 1)
        if stored_scopes and stored_scopes != SCOPES:
            log.warning(
                "OAuth scopes changed (old: %s, new: %s) — clearing old credentials. "
                "User must re-authenticate.",
                stored_scopes,
                SCOPES,
            )
            self.clear_credentials()
            return None
        
        credentials = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=stored_scopes,
        )
        return credentials

    def clear_credentials(self) -> None:
        """Delete credentials from the database."""
        conn = get_connection()
        conn.execute("DELETE FROM oauth_credentials WHERE id = 1")
        conn.commit()
        log.info("OAuth credentials cleared from database")

    def _save_oauth_state(self, state: str, code_verifier: str) -> None:
        """Save OAuth state and PKCE code_verifier to database.
        
        Args:
            state: OAuth state parameter (for CSRF protection)
            code_verifier: PKCE code verifier (for token exchange)
        """
        conn = get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO oauth_state (id, state, code_verifier, created_at)
            VALUES (1, ?, ?, datetime('now'))
            """,
            (state, code_verifier),
        )
        conn.commit()

    def _verify_oauth_state(self, state: str) -> str:
        """Verify OAuth state parameter and return code_verifier.
        
        Args:
            state: OAuth state parameter from callback
            
        Returns:
            code_verifier: PKCE code verifier for token exchange
            
        Raises:
            ValueError: If state is invalid or missing
        """
        conn = get_connection()
        row = conn.execute(
            "SELECT state, code_verifier FROM oauth_state WHERE id = 1"
        ).fetchone()
        
        if not row:
            raise ValueError("OAuth state not found - authorization may have expired")
        
        if row["state"] != state:
            raise ValueError("Invalid OAuth state parameter - possible CSRF attack")
        
        # Clear the state after successful verification (one-time use)
        conn.execute("DELETE FROM oauth_state WHERE id = 1")
        conn.commit()
        
        return row["code_verifier"]

    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        credentials = self.get_credentials()
        return credentials is not None

    def get_http(self) -> AuthorizedSession:
        """Get an AuthorizedSession with auto-refresh.

        Raises RuntimeError if not authenticated.
        """
        credentials = self.get_credentials()
        if credentials is None:
            raise RuntimeError("not authenticated: call handle_callback() first")

        # Refresh if expired (with lock and double-check)
        if credentials.expired and credentials.refresh_token:
            with self._refresh_lock:
                # Double-check after acquiring lock
                credentials = self.get_credentials()
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    self.save_credentials(credentials)
                    log.info("OAuth token refreshed")

        return AuthorizedSession(credentials)

    def migrate_from_pickle(self, pickle_path: str = "credentials.pickle") -> bool:
        """Migrate credentials from pickle file to database.

        Returns True if migration happened, False if no pickle found.
        """
        import pickle
        from pathlib import Path

        pickle_file = Path(pickle_path)
        if not pickle_file.exists():
            return False

        # Check if DB already has credentials
        if self.is_authenticated():
            log.info("credentials already in database — skipping pickle migration")
            return False

        # Load from pickle
        try:
            with open(pickle_file, "rb") as f:
                credentials = pickle.load(f)

            # Save to DB
            self.save_credentials(credentials)
            log.warning(
                "migrated OAuth credentials from %s to database (pickle file NOT deleted — remove manually)",
                pickle_path,
            )
            return True
        except Exception as e:
            log.error("failed to migrate credentials from pickle: %s", e)
            return False
