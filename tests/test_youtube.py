"""Tests for sortarr.core.youtube — YouTube Data API v3 client."""

import pytest
from unittest.mock import MagicMock, patch

from sortarr.core.youtube import (
    YouTubeAPIClient,
    get_quota_used,
    reset_quota,
    _increment_quota,
)


@pytest.fixture(autouse=True)
def reset_quota_before_each():
    """Reset quota counter before each test."""
    reset_quota()
    yield
    reset_quota()


@pytest.fixture
def mock_http():
    """Mock AuthorizedSession."""
    return MagicMock()


@pytest.fixture
def client():
    """Create a YouTubeAPIClient instance."""
    return YouTubeAPIClient()


class TestQuotaTracking:
    """Test quota tracking functions."""
    
    def test_get_quota_used_initial(self):
        """Quota starts at 0."""
        assert get_quota_used() == 0
    
    def test_increment_quota(self):
        """Quota increments correctly."""
        _increment_quota(1)
        assert get_quota_used() == 1
        _increment_quota(50)
        assert get_quota_used() == 51
    
    def test_reset_quota(self):
        """Reset sets quota back to 0."""
        _increment_quota(100)
        assert get_quota_used() == 100
        reset_quota()
        assert get_quota_used() == 0


class TestGetSubscriptions:
    """Test get_subscriptions method."""
    
    @patch("sortarr.core.youtube.build")
    def test_get_subscriptions_basic(self, mock_build, client, mock_http):
        """get_subscriptions calls correct API endpoint."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.subscriptions().list.return_value = mock_request
        mock_request.execute.return_value = {"items": [{"id": "sub1"}]}
        
        result = client.get_subscriptions(mock_http)
        
        mock_build.assert_called_once_with("youtube", "v3", http=mock_http)
        mock_youtube.subscriptions().list.assert_called_once_with(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=None
        )
        assert result == {"items": [{"id": "sub1"}]}
    
    @patch("sortarr.core.youtube.build")
    def test_get_subscriptions_with_pagination(self, mock_build, client, mock_http):
        """get_subscriptions passes page_token."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.subscriptions().list.return_value = mock_request
        mock_request.execute.return_value = {"items": [], "nextPageToken": "token2"}
        
        result = client.get_subscriptions(mock_http, page_token="token1", max_results=25)
        
        mock_youtube.subscriptions().list.assert_called_once_with(
            part="snippet",
            mine=True,
            maxResults=25,
            pageToken="token1"
        )
        assert result["nextPageToken"] == "token2"
    
    @patch("sortarr.core.youtube.build")
    def test_get_subscriptions_quota_cost(self, mock_build, client, mock_http):
        """get_subscriptions costs 1 quota unit."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.subscriptions().list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        
        initial_quota = get_quota_used()
        client.get_subscriptions(mock_http)
        
        assert get_quota_used() == initial_quota + 1


class TestGetActivities:
    """Test get_activities method."""
    
    @patch("sortarr.core.youtube.build")
    def test_get_activities_basic(self, mock_build, client, mock_http):
        """get_activities calls correct API endpoint."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.activities().list.return_value = mock_request
        mock_request.execute.return_value = {"items": [{"id": "act1"}]}
        
        result = client.get_activities(
            mock_http,
            channel_id="UC123",
            published_after="2024-01-01T00:00:00Z"
        )
        
        mock_build.assert_called_once_with("youtube", "v3", http=mock_http)
        mock_youtube.activities().list.assert_called_once_with(
            part="snippet,contentDetails",
            channelId="UC123",
            publishedAfter="2024-01-01T00:00:00Z",
            maxResults=50,
            pageToken=None
        )
        assert result == {"items": [{"id": "act1"}]}
    
    @patch("sortarr.core.youtube.build")
    def test_get_activities_quota_cost(self, mock_build, client, mock_http):
        """get_activities costs 1 quota unit."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.activities().list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        
        initial_quota = get_quota_used()
        client.get_activities(mock_http, "UC123", "2024-01-01T00:00:00Z")
        
        assert get_quota_used() == initial_quota + 1


class TestGetVideosBatch:
    """Test get_videos_batch method."""
    
    @patch("sortarr.core.youtube.build")
    def test_get_videos_batch_basic(self, mock_build, client, mock_http):
        """get_videos_batch calls correct API endpoint."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.videos().list.return_value = mock_request
        mock_request.execute.return_value = {"items": [{"id": "vid1"}]}
        
        result = client.get_videos_batch(mock_http, "vid1,vid2,vid3")
        
        mock_build.assert_called_once_with("youtube", "v3", http=mock_http)
        mock_youtube.videos().list.assert_called_once_with(
            part="contentDetails",
            id="vid1,vid2,vid3"
        )
        assert result == {"items": [{"id": "vid1"}]}
    
    @patch("sortarr.core.youtube.build")
    def test_get_videos_batch_quota_cost(self, mock_build, client, mock_http):
        """get_videos_batch costs 1 quota unit."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.videos().list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        
        initial_quota = get_quota_used()
        client.get_videos_batch(mock_http, "vid1,vid2")
        
        assert get_quota_used() == initial_quota + 1


class TestGetPlaylists:
    """Test get_playlists method."""
    
    @patch("sortarr.core.youtube.build")
    def test_get_playlists_basic(self, mock_build, client, mock_http):
        """get_playlists calls correct API endpoint."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.playlists().list.return_value = mock_request
        mock_request.execute.return_value = {"items": [{"id": "pl1"}]}
        
        result = client.get_playlists(mock_http)
        
        mock_build.assert_called_once_with("youtube", "v3", http=mock_http)
        mock_youtube.playlists().list.assert_called_once_with(
            part="snippet",
            mine=True,
            maxResults=50
        )
        assert result == {"items": [{"id": "pl1"}]}
    
    @patch("sortarr.core.youtube.build")
    def test_get_playlists_quota_cost(self, mock_build, client, mock_http):
        """get_playlists costs 1 quota unit."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.playlists().list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        
        initial_quota = get_quota_used()
        client.get_playlists(mock_http)
        
        assert get_quota_used() == initial_quota + 1


class TestInsertPlaylistItem:
    """Test insert_playlist_item method."""
    
    @patch("sortarr.core.youtube.build")
    def test_insert_playlist_item_basic(self, mock_build, client, mock_http):
        """insert_playlist_item calls correct API endpoint."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.playlistItems().insert.return_value = mock_request
        mock_request.execute.return_value = {"id": "item1", "snippet": {}}
        
        result = client.insert_playlist_item(mock_http, "PL123", "vid456")
        
        mock_build.assert_called_once_with("youtube", "v3", http=mock_http)
        mock_youtube.playlistItems().insert.assert_called_once_with(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": "PL123",
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": "vid456"
                    }
                }
            }
        )
        assert result == {"id": "item1", "snippet": {}}
    
    @patch("sortarr.core.youtube.build")
    def test_insert_playlist_item_quota_cost(self, mock_build, client, mock_http):
        """insert_playlist_item costs 50 quota units."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.playlistItems().insert.return_value = mock_request
        mock_request.execute.return_value = {"id": "item1"}
        
        initial_quota = get_quota_used()
        client.insert_playlist_item(mock_http, "PL123", "vid456")
        
        assert get_quota_used() == initial_quota + 50


class TestGetPlaylistItems:
    """Test get_playlist_items method."""
    
    @patch("sortarr.core.youtube.build")
    def test_get_playlist_items_basic(self, mock_build, client, mock_http):
        """get_playlist_items calls correct API endpoint."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.playlistItems().list.return_value = mock_request
        mock_request.execute.return_value = {"items": [{"id": "item1"}]}
        
        result = client.get_playlist_items(mock_http, "PL123")
        
        mock_build.assert_called_once_with("youtube", "v3", http=mock_http)
        mock_youtube.playlistItems().list.assert_called_once_with(
            part="snippet",
            playlistId="PL123",
            maxResults=50,
            pageToken=None
        )
        assert result == {"items": [{"id": "item1"}]}
    
    @patch("sortarr.core.youtube.build")
    def test_get_playlist_items_with_pagination(self, mock_build, client, mock_http):
        """get_playlist_items passes page_token."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.playlistItems().list.return_value = mock_request
        mock_request.execute.return_value = {"items": [], "nextPageToken": "token2"}
        
        result = client.get_playlist_items(
            mock_http,
            "PL123",
            page_token="token1",
            max_results=25
        )
        
        mock_youtube.playlistItems().list.assert_called_once_with(
            part="snippet",
            playlistId="PL123",
            maxResults=25,
            pageToken="token1"
        )
        assert result["nextPageToken"] == "token2"
    
    @patch("sortarr.core.youtube.build")
    def test_get_playlist_items_quota_cost(self, mock_build, client, mock_http):
        """get_playlist_items costs 1 quota unit."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_request = MagicMock()
        mock_youtube.playlistItems().list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        
        initial_quota = get_quota_used()
        client.get_playlist_items(mock_http, "PL123")
        
        assert get_quota_used() == initial_quota + 1



