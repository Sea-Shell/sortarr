"""
sortarr.core.youtube — YouTube Data API v3 client.

Wraps google-api-python-client with quota tracking and token refresh.
All API calls go through this client.
"""

import logging
import threading
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
import httplib2

log = logging.getLogger("sortarr.core.youtube")

# Lock for thread-safe quota operations
_quota_lock = threading.Lock()


def get_quota_used() -> int:
    """Get current quota usage from database."""
    from sortarr.db.repository import config

    value = config.get_config_value("quota_used", "0")
    return int(value) if value else 0


def reset_quota() -> None:
    """Reset quota counter in database."""
    from sortarr.db.repository import config

    config.set_config("quota_used", "0")
    log.info("quota counter reset")


def _increment_quota(cost: int) -> None:
    """Increment quota counter atomically in database."""
    from sortarr.db.connection import get_connection

    with _quota_lock:
        conn = get_connection()
        # Initialize if not exists
        conn.execute("""
            INSERT INTO app_config (key, value) VALUES ('quota_used', '0')
            ON CONFLICT(key) DO NOTHING
        """)
        # Atomic increment
        conn.execute(
            """
            UPDATE app_config 
            SET value = CAST(CAST(value AS INTEGER) + ? AS TEXT)
            WHERE key = 'quota_used'
        """,
            (cost,),
        )
        conn.commit()


class YouTubeAPIClient:
    """YouTube Data API v3 client with quota tracking.

    All methods accept a `credentials` parameter for building authorized HTTP clients.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize the client.

        api_key is optional — OAuth credentials are passed via credentials parameter.
        """
        self.api_key = api_key

    def _build_http(self, credentials: Credentials) -> AuthorizedHttp:
        """Build an authorized HTTP client using httplib2.
        
        This avoids the 'body' parameter incompatibility between
        google-api-python-client and requests.Session.
        """
        http = httplib2.Http()
        return AuthorizedHttp(credentials, http=http)

    def get_subscriptions(
        self,
        credentials: Credentials,
        page_token: str | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Fetch user's YouTube subscriptions.

        Costs 1 quota unit per call.
        Returns: {"items": [...], "nextPageToken": "..."}
        """
        _increment_quota(1)
        http = self._build_http(credentials)
        youtube = build("youtube", "v3", http=http)
        request = youtube.subscriptions().list(
            part="snippet", mine=True, maxResults=max_results, pageToken=page_token
        )
        return request.execute()

    def get_activities(
        self,
        credentials: Credentials,
        channel_id: str,
        published_after: str,
        page_token: str | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Fetch activities for a channel.

        Costs 1 quota unit per call.
        published_after: ISO 8601 timestamp (e.g., "2024-01-01T00:00:00Z")
        Returns: {"items": [...], "nextPageToken": "..."}
        """
        _increment_quota(1)
        http = self._build_http(credentials)
        youtube = build("youtube", "v3", http=http)
        request = youtube.activities().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            publishedAfter=published_after,
            maxResults=max_results,
            pageToken=page_token,
        )
        return request.execute()

    def get_videos_batch(
        self, credentials: Credentials, video_ids_csv: str
    ) -> dict[str, Any]:
        """Fetch video details for up to 50 video IDs.

        Costs 1 quota unit per call.
        video_ids_csv: comma-separated video IDs (max 50)
        Returns: {"items": [...]}
        """
        _increment_quota(1)
        http = self._build_http(credentials)
        youtube = build("youtube", "v3", http=http)
        request = youtube.videos().list(part="contentDetails", id=video_ids_csv)
        return request.execute()

    def get_playlists(
        self, credentials: Credentials, max_results: int = 50
    ) -> dict[str, Any]:
        """Fetch user's YouTube playlists.

        Costs 1 quota unit per call.
        Returns: {"items": [...]}
        """
        _increment_quota(1)
        http = self._build_http(credentials)
        youtube = build("youtube", "v3", http=http)
        request = youtube.playlists().list(
            part="snippet", mine=True, maxResults=max_results
        )
        return request.execute()

    def insert_playlist_item(
        self, credentials: Credentials, playlist_id: str, video_id: str
    ) -> dict[str, Any]:
        """Insert a video into a playlist.

        Costs 50 quota units per call.
        Returns: {"id": "...", "snippet": {...}}
        """
        _increment_quota(50)
        http = self._build_http(credentials)
        youtube = build("youtube", "v3", http=http)
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        )
        return request.execute()

    def get_playlist_items(
        self,
        credentials: Credentials,
        playlist_id: str,
        page_token: str | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Fetch items in a playlist.

        Costs 1 quota unit per call.
        Returns: {"items": [...], "nextPageToken": "..."}
        """
        _increment_quota(1)
        http = self._build_http(credentials)
        youtube = build("youtube", "v3", http=http)
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token,
        )
        return request.execute()
