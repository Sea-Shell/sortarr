"""
sortarr.core.youtube — YouTube Data API v3 client.

Wraps google-api-python-client with quota tracking and token refresh.
All API calls go through this client.
"""

import logging
from typing import Any

from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build

log = logging.getLogger("sortarr.core.youtube")

# Module-level quota counter
_quota_used = 0


def get_quota_used() -> int:
    """Get the current quota usage for today."""
    return _quota_used


def reset_quota() -> None:
    """Reset the quota counter (called at midnight PT or on app restart)."""
    global _quota_used
    _quota_used = 0
    log.info("quota counter reset")


def _increment_quota(cost: int) -> None:
    """Increment the quota counter."""
    global _quota_used
    _quota_used += cost


class YouTubeAPIClient:
    """YouTube Data API v3 client with quota tracking.
    
    All methods accept an `http` parameter (AuthorizedSession) for token refresh.
    """
    
    def __init__(self, api_key: str | None = None):
        """Initialize the client.
        
        api_key is optional — OAuth credentials are passed via http parameter.
        """
        self.api_key = api_key
    
    def get_subscriptions(
        self,
        http: AuthorizedSession,
        page_token: str | None = None,
        max_results: int = 50
    ) -> dict[str, Any]:
        """Fetch user's YouTube subscriptions.
        
        Costs 1 quota unit per call.
        Returns: {"items": [...], "nextPageToken": "..."}
        """
        _increment_quota(1)
        youtube = build("youtube", "v3", http=http)
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=max_results,
            pageToken=page_token
        )
        return request.execute()
    
    def get_activities(
        self,
        http: AuthorizedSession,
        channel_id: str,
        published_after: str,
        page_token: str | None = None,
        max_results: int = 50
    ) -> dict[str, Any]:
        """Fetch activities for a channel.
        
        Costs 1 quota unit per call.
        published_after: ISO 8601 timestamp (e.g., "2024-01-01T00:00:00Z")
        Returns: {"items": [...], "nextPageToken": "..."}
        """
        _increment_quota(1)
        youtube = build("youtube", "v3", http=http)
        request = youtube.activities().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            publishedAfter=published_after,
            maxResults=max_results,
            pageToken=page_token
        )
        return request.execute()
    
    def get_videos_batch(
        self,
        http: AuthorizedSession,
        video_ids_csv: str
    ) -> dict[str, Any]:
        """Fetch video details for up to 50 video IDs.
        
        Costs 1 quota unit per call.
        video_ids_csv: comma-separated video IDs (max 50)
        Returns: {"items": [...]}
        """
        _increment_quota(1)
        youtube = build("youtube", "v3", http=http)
        request = youtube.videos().list(
            part="contentDetails",
            id=video_ids_csv
        )
        return request.execute()
    
    def get_playlists(
        self,
        http: AuthorizedSession,
        max_results: int = 50
    ) -> dict[str, Any]:
        """Fetch user's YouTube playlists.
        
        Costs 1 quota unit per call.
        Returns: {"items": [...]}
        """
        _increment_quota(1)
        youtube = build("youtube", "v3", http=http)
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=max_results
        )
        return request.execute()
    
    def insert_playlist_item(
        self,
        http: AuthorizedSession,
        playlist_id: str,
        video_id: str
    ) -> dict[str, Any]:
        """Insert a video into a playlist.
        
        Costs 50 quota units per call.
        Returns: {"id": "...", "snippet": {...}}
        """
        _increment_quota(50)
        youtube = build("youtube", "v3", http=http)
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        return request.execute()
    
    def get_playlist_items(
        self,
        http: AuthorizedSession,
        playlist_id: str,
        page_token: str | None = None,
        max_results: int = 50
    ) -> dict[str, Any]:
        """Fetch items in a playlist.
        
        Costs 1 quota unit per call.
        Returns: {"items": [...], "nextPageToken": "..."}
        """
        _increment_quota(1)
        youtube = build("youtube", "v3", http=http)
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token
        )
        return request.execute()

