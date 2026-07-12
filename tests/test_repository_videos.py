"""Unit tests for sortarr.db.repository.videos"""

import pytest
from sortarr.db.connection import init_db, close_db
from sortarr.db.migrations import init_db as apply_schema
from sortarr.db.repository import videos
from sortarr.models.youtube import Video


@pytest.fixture
def db():
    """Initialize an in-memory database for testing."""
    conn = init_db(":memory:")
    apply_schema(conn)
    yield conn
    close_db()


def test_insert_and_get_video(db):
    """Test inserting and retrieving a video."""
    video = Video(
        video_id="test123",
        title="Test Video",
        channel_id="channel1",
        channel_title="Test Channel",
        published_at="2024-01-01T00:00:00Z",
        duration_seconds=300,
        pipeline_id="pipeline1",
        playlist_id="playlist1"
    )
    
    videos.insert_video(video)
    retrieved = videos.get_video("test123")
    
    assert retrieved is not None
    assert retrieved.video_id == "test123"
    assert retrieved.title == "Test Video"
    assert retrieved.duration_seconds == 300


def test_video_exists(db):
    """Test video_exists check."""
    video = Video(
        video_id="test456",
        title="Test",
        channel_id="ch1",
        channel_title="Ch",
        published_at="2024-01-01T00:00:00Z",
        pipeline_id="pipe1",
        playlist_id="play1"
    )
    
    assert not videos.video_exists("test456", "pipe1")
    videos.insert_video(video)
    assert videos.video_exists("test456", "pipe1")


def test_video_exists_different_pipeline(db):
    """Test video_exists is pipeline-specific."""
    video = Video(
        video_id="test789",
        title="Test",
        channel_id="ch1",
        channel_title="Ch",
        published_at="2024-01-01T00:00:00Z",
        pipeline_id="pipe1",
        playlist_id="play1"
    )
    
    videos.insert_video(video)
    assert videos.video_exists("test789", "pipe1")
    assert not videos.video_exists("test789", "pipe2")


def test_search_videos_single_insert(db):
    """Test searching for a video (schema allows only one insert per video_id)."""
    video = Video(
        video_id="unique123",
        title="Unique Video",
        channel_id="ch1",
        channel_title="Ch",
        published_at="2024-01-01T00:00:00Z",
        pipeline_id="pipe1",
        playlist_id="play1"
    )
    
    videos.insert_video(video)
    
    results = videos.search_videos("unique123")
    assert len(results) == 1
    assert results[0]["video_id"] == "unique123"
    assert results[0]["pipeline_id"] == "pipe1"


def test_get_video_nonexistent(db):
    """Test get_video returns None for nonexistent video."""
    result = videos.get_video("nonexistent")
    assert result is None


def test_videos_parameterized_queries(db):
    """Test that queries are parameterized (SQL injection safe)."""
    malicious_id = "test'; DROP TABLE videos; --"
    video = Video(
        video_id=malicious_id,
        title="Test",
        channel_id="ch1",
        channel_title="Ch",
        published_at="2024-01-01T00:00:00Z",
        pipeline_id="pipe1",
        playlist_id="play1"
    )
    
    videos.insert_video(video)
    assert videos.video_exists(malicious_id, "pipe1")
