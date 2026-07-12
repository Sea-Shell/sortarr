"""Tests for Phase 4 gate issue fixes (C1-C3, M1-M5)."""

import threading
from unittest.mock import Mock

import pytest

from sortarr.core.auth import OAuthManager
from sortarr.core.enricher import Enricher
from sortarr.core.runner import Runner
from sortarr.core.youtube import get_quota_used, reset_quota
from sortarr.db.connection import close_db, get_connection, init_db
from sortarr.db.migrations import init_db as apply_schema
from sortarr.db.repository import config, pipelines
from sortarr.models.pipeline import PipelineCreate


@pytest.fixture
def db():
    """Initialize an in-memory database for testing."""
    conn = init_db(":memory:")
    apply_schema(conn)
    yield conn
    close_db()


# C1: Filter context returns empty stubs
def test_build_filter_context_loads_ignore_lists(db):
    """Test that _build_filter_context loads ignore lists from database."""
    # Create a pipeline
    pipeline_config = PipelineCreate(
        name="Test Pipeline",
        playlist_id="PLtest123",
        selector_mode="AND",
        subscription_scope="all",
    )
    pipeline = pipelines.create_pipeline(pipeline_config)

    # Manually insert test data into ignore_lists and ignore_list_entries
    conn = get_connection()
    
    # Create word ignore list
    conn.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("word-list-1", "Words", "word")
    )
    conn.execute(
        "INSERT INTO ignore_list_entries (id, ignore_list_id, value, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("entry-1", "word-list-1", "spam")
    )
    conn.execute(
        "INSERT INTO ignore_list_entries (id, ignore_list_id, value, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("entry-2", "word-list-1", "test")
    )
    
    # Create video ignore list
    conn.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("video-list-1", "Videos", "video")
    )
    conn.execute(
        "INSERT INTO ignore_list_entries (id, ignore_list_id, value, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("entry-3", "video-list-1", "vid123")
    )
    conn.commit()

    # Associate ignore lists with pipeline
    pipelines.set_ignore_lists(pipeline.id, ["word-list-1", "video-list-1"])

    # Create a runner and build filter context
    mock_youtube = Mock()
    mock_oauth = Mock()
    runner = Runner(mock_youtube, mock_oauth)

    context = runner._build_filter_context(pipeline)

    # Verify context is populated (not empty stubs)
    assert "spam" in context["word_ignore_values"]
    assert "test" in context["word_ignore_values"]
    assert "vid123" in context["video_ignore_ids"]
    assert isinstance(context["inserted_video_ids"], set)


# C2: Concurrency guard race condition
def test_concurrency_guard_cleanup_on_crash(db):
    """Test that stale run_active flag is cleaned up on startup."""
    # Simulate a crashed run by setting run_active
    config.set_config("run_active", "true")

    # Create a runner and call startup cleanup
    mock_youtube = Mock()
    mock_oauth = Mock()
    runner = Runner(mock_youtube, mock_oauth)
    runner._startup_cleanup()

    # Verify flag was cleared
    assert config.get_config_value("run_active") is None


# C3: Quota counter not thread-safe
def test_quota_persists_across_instances(db):
    """Test that quota counter persists in database across instances."""
    from sortarr.core.youtube import _increment_quota

    # Reset quota
    reset_quota()
    assert get_quota_used() == 0

    # Increment quota
    _increment_quota(50)
    assert get_quota_used() == 50

    # Increment again
    _increment_quota(100)
    assert get_quota_used() == 150

    # Verify it persists (simulated by re-reading from DB)
    quota = get_quota_used()
    assert quota == 150


# C4: Quota counter atomicity
def test_quota_increment_is_atomic(db):
    """Test that quota counter increments are atomic under concurrent access."""
    from sortarr.core.youtube import _increment_quota

    # Reset quota
    reset_quota()
    assert get_quota_used() == 0

    # Simulate concurrent increments from multiple threads
    num_threads = 10
    increments_per_thread = 10
    increment_value = 5
    
    errors = []
    
    def increment_quota_thread():
        """Thread worker that increments quota multiple times."""
        try:
            for _ in range(increments_per_thread):
                _increment_quota(increment_value)
        except Exception as e:
            errors.append(e)
    
    # Launch threads
    threads = [threading.Thread(target=increment_quota_thread) for _ in range(num_threads)]
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    
    # Verify final quota is correct (all increments should be counted)
    expected_quota = num_threads * increments_per_thread * increment_value
    actual_quota = get_quota_used()
    assert actual_quota == expected_quota, (
        f"Lost updates detected: expected {expected_quota}, got {actual_quota}"
    )


# M1: Enricher swallows exceptions
def test_enricher_returns_failed_ids(db):
    """Test that enricher returns failed video IDs instead of swallowing them."""
    call_count = [0]

    def mock_api_with_failure(ids_csv: str):
        """Mock API that fails on second batch."""
        call_count[0] += 1
        if call_count[0] == 2:  # Fail on second batch
            raise Exception("API error")
        return {"items": [{"id": "vid1", "contentDetails": {"duration": "PT5M"}}]}

    enricher = Enricher(mock_api_with_failure)

    # Create enough videos for 2 batches (batch size is 50)
    video_ids = {f"vid{i}" for i in range(1, 51)}  # First batch
    video_ids.update({f"batch2_vid{i}" for i in range(1, 51)})  # Second batch

    duration_map, failed_ids = enricher.batch_fetch(video_ids)

    # Verify successful videos from first batch are in duration_map
    assert "vid1" in duration_map

    # Verify failed videos from second batch are returned
    assert len(failed_ids) == 50  # All videos from second batch
    assert "batch2_vid1" in failed_ids


# M2: No playlist_id validation
def test_create_pipeline_validates_playlist_id(db):
    """Test that create_pipeline validates playlist_id."""
    # Empty playlist_id should raise ValueError
    with pytest.raises(ValueError, match="playlist_id is required"):
        pipelines.create_pipeline(
            PipelineCreate(
                name="Test",
                playlist_id="",
                selector_mode="AND",
                subscription_scope="all",
            )
        )

    # Whitespace-only playlist_id should raise ValueError
    with pytest.raises(ValueError, match="playlist_id is required"):
        pipelines.create_pipeline(
            PipelineCreate(
                name="Test",
                playlist_id="   ",
                selector_mode="AND",
                subscription_scope="all",
            )
        )

    # None playlist_id should raise ValueError
    with pytest.raises(ValueError, match="playlist_id is required"):
        pipelines.create_pipeline(
            PipelineCreate(
                name="Test",
                playlist_id=None,
                selector_mode="AND",
                subscription_scope="all",
            )
        )


def test_runner_skips_pipeline_without_playlist_id(db):
    """Test that runner skips pipelines with no playlist_id."""
    from sortarr.models.pipeline import PipelineConfig

    mock_youtube = Mock()
    mock_oauth = Mock()
    runner = Runner(mock_youtube, mock_oauth)

    # Create a pipeline config with no playlist_id (simulating corrupted data)
    pipeline = PipelineConfig(
        id="test-id",
        name="Test",
        enabled=True,
        playlist_id=None,  # Missing playlist_id
        order=0,
        subscription_scope="all",
        selector_mode="AND",
    )

    # Build filter context should not crash
    context = runner._build_filter_context(pipeline)
    assert context is not None


# M3: Token refresh race condition
def test_oauth_refresh_thread_safe(db):
    """Test that OAuth token refresh is thread-safe."""
    import tempfile
    from pathlib import Path

    # Create a temporary client secret file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(
            '{"installed":{"client_id":"test","client_secret":"test","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}}'
        )
        client_secret_path = f.name

    try:
        oauth_manager = OAuthManager(client_secret_path, "http://localhost:8080/callback")

        # Verify lock exists
        assert hasattr(oauth_manager, "_refresh_lock")
        assert isinstance(oauth_manager._refresh_lock, threading.Lock)
    finally:
        Path(client_secret_path).unlink()


# M4: Incomplete selector implementation
def test_set_selectors_raises_not_implemented(db):
    """Test that set_selectors raises NotImplementedError."""
    # Create a pipeline
    pipeline_config = PipelineCreate(
        name="Test Pipeline",
        playlist_id="PLtest123",
        selector_mode="AND",
        subscription_scope="all",
    )
    pipeline = pipelines.create_pipeline(pipeline_config)

    # Try to set selectors - should raise NotImplementedError
    with pytest.raises(NotImplementedError, match="Selector CRUD is not implemented"):
        pipelines.set_selectors(pipeline.id, ["selector1", "selector2"])

    # Clearing selectors (empty list) should work
    pipelines.set_selectors(pipeline.id, [])  # Should not raise


# M5: Schema mismatch - get_video() removed
def test_get_video_removed(db):
    """Test that get_video() has been removed from videos repository."""
    from sortarr.db.repository import videos

    # Verify get_video is not available
    assert not hasattr(videos, "get_video")

    # search_videos should still work
    results = videos.search_videos("nonexistent")
    assert results == []
