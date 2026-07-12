"""Unit tests for sortarr.db.repository.activities."""

from datetime import UTC, datetime, timedelta

import pytest

from sortarr.db.connection import init_db, close_db
from sortarr.db.migrations import init_db as apply_schema
from sortarr.db.repository import activities
from sortarr.models.youtube import Activity


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    conn = init_db(":memory:")
    apply_schema(conn)
    yield conn
    close_db()


def test_upsert_activities_insert(db):
    """Test inserting new activities."""
    acts = [
        Activity(
            video_id="vid1",
            title="Test Video 1",
            description="Description 1",
            published_at="2026-07-01T10:00:00Z",
            channel_id="ch1",
            channel_title="Channel 1",
            subscription_id="sub1",
            activity_type="upload",
            duration_seconds=120,
        ),
        Activity(
            video_id="vid2",
            title="Test Video 2",
            description="Description 2",
            published_at="2026-07-02T10:00:00Z",
            channel_id="ch2",
            channel_title="Channel 2",
            subscription_id="sub2",
            activity_type="upload",
            duration_seconds=240,
        ),
    ]

    activities.upsert_activities(acts)

    # Verify both were inserted
    result = activities.get_activities()
    assert len(result) == 2
    assert result[0].video_id == "vid2"  # DESC order by published_at
    assert result[1].video_id == "vid1"


def test_upsert_activities_idempotency(db):
    """Test that upserting the same activity twice doesn't create duplicates."""
    act = Activity(
        video_id="vid1",
        title="Original Title",
        description="Original Description",
        published_at="2026-07-01T10:00:00Z",
        channel_id="ch1",
        channel_title="Channel 1",
        subscription_id="sub1",
        activity_type="upload",
        duration_seconds=120,
    )

    # Insert once
    activities.upsert_activities([act])
    result1 = activities.get_activities()
    assert len(result1) == 1
    assert result1[0].title == "Original Title"

    # Update and insert again
    act.title = "Updated Title"
    activities.upsert_activities([act])

    # Should still be only 1 row, with updated title
    result2 = activities.get_activities()
    assert len(result2) == 1
    assert result2[0].title == "Updated Title"
    assert result2[0].video_id == "vid1"


def test_upsert_activities_duration_coalesce(db):
    """Test that duration is preserved if new value is None."""
    act = Activity(
        video_id="vid1",
        title="Test Video",
        description="Description",
        published_at="2026-07-01T10:00:00Z",
        channel_id="ch1",
        channel_title="Channel 1",
        subscription_id="sub1",
        activity_type="upload",
        duration_seconds=120,
    )

    # Insert with duration
    activities.upsert_activities([act])
    result1 = activities.get_activities()
    assert result1[0].duration_seconds == 120

    # Update with None duration
    act.duration_seconds = None
    activities.upsert_activities([act])

    # Duration should be preserved (COALESCE)
    result2 = activities.get_activities()
    assert result2[0].duration_seconds == 120


def test_get_activities_with_subscription_filter(db):
    """Test filtering activities by subscription IDs."""
    acts = [
        Activity(
            video_id="vid1",
            title="Video 1",
            description="",
            published_at="2026-07-01T10:00:00Z",
            channel_id="ch1",
            channel_title="Channel 1",
            subscription_id="sub1",
            activity_type="upload",
        ),
        Activity(
            video_id="vid2",
            title="Video 2",
            description="",
            published_at="2026-07-02T10:00:00Z",
            channel_id="ch2",
            channel_title="Channel 2",
            subscription_id="sub2",
            activity_type="upload",
        ),
        Activity(
            video_id="vid3",
            title="Video 3",
            description="",
            published_at="2026-07-03T10:00:00Z",
            channel_id="ch3",
            channel_title="Channel 3",
            subscription_id="sub3",
            activity_type="upload",
        ),
    ]

    activities.upsert_activities(acts)

    # Filter by sub1 and sub3
    result = activities.get_activities(subscription_ids=["sub1", "sub3"])
    assert len(result) == 2
    video_ids = {r.video_id for r in result}
    assert video_ids == {"vid1", "vid3"}


def test_get_activities_without_filter(db):
    """Test getting all activities without filter."""
    acts = [
        Activity(
            video_id="vid1",
            title="Video 1",
            description="",
            published_at="2026-07-01T10:00:00Z",
            channel_id="ch1",
            channel_title="Channel 1",
            subscription_id="sub1",
            activity_type="upload",
        ),
        Activity(
            video_id="vid2",
            title="Video 2",
            description="",
            published_at="2026-07-02T10:00:00Z",
            channel_id="ch2",
            channel_title="Channel 2",
            subscription_id="sub2",
            activity_type="upload",
        ),
    ]

    activities.upsert_activities(acts)
    result = activities.get_activities()
    assert len(result) == 2


def test_get_cached_duration_exists(db):
    """Test getting cached duration for an existing video."""
    act = Activity(
        video_id="vid1",
        title="Test Video",
        description="",
        published_at="2026-07-01T10:00:00Z",
        channel_id="ch1",
        channel_title="Channel 1",
        subscription_id="sub1",
        activity_type="upload",
        duration_seconds=300,
    )

    activities.upsert_activities([act])
    duration = activities.get_cached_duration("vid1")
    assert duration == 300


def test_get_cached_duration_not_exists(db):
    """Test getting cached duration for a non-existent video."""
    duration = activities.get_cached_duration("nonexistent")
    assert duration is None


def test_update_duration(db):
    """Test updating duration for a cached activity."""
    act = Activity(
        video_id="vid1",
        title="Test Video",
        description="",
        published_at="2026-07-01T10:00:00Z",
        channel_id="ch1",
        channel_title="Channel 1",
        subscription_id="sub1",
        activity_type="upload",
        duration_seconds=None,
    )

    activities.upsert_activities([act])
    assert activities.get_cached_duration("vid1") is None

    # Update duration
    activities.update_duration("vid1", 450)
    assert activities.get_cached_duration("vid1") == 450


def test_prune_old_entries(db):
    """Test pruning old entries from the cache."""
    conn = db

    # Insert old entry (35 days ago)
    old_date = (datetime.now(UTC) - timedelta(days=35)).isoformat()
    conn.execute(
        """
        INSERT INTO activity_cache (
            video_id, title, description, published_at,
            channel_id, channel_title, subscription_id,
            video_type, duration_seconds, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "old_vid",
            "Old Video",
            "",
            "2026-06-01T10:00:00Z",
            "ch1",
            "Channel 1",
            "sub1",
            "upload",
            120,
            old_date,
        ),
    )

    # Insert recent entry (5 days ago)
    recent_date = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    conn.execute(
        """
        INSERT INTO activity_cache (
            video_id, title, description, published_at,
            channel_id, channel_title, subscription_id,
            video_type, duration_seconds, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "recent_vid",
            "Recent Video",
            "",
            "2026-07-07T10:00:00Z",
            "ch2",
            "Channel 2",
            "sub2",
            "upload",
            240,
            recent_date,
        ),
    )
    conn.commit()

    # Prune entries older than 30 days
    deleted = activities.prune_old_entries(retention_days=30)
    assert deleted == 1

    # Verify only recent entry remains
    result = activities.get_activities()
    assert len(result) == 1
    assert result[0].video_id == "recent_vid"


def test_get_cache_stats(db):
    """Test getting cache statistics."""
    # Empty cache
    stats = activities.get_cache_stats()
    assert stats["count"] == 0
    assert stats["oldest"] is None
    assert stats["newest"] is None

    # Add some activities
    acts = [
        Activity(
            video_id="vid1",
            title="Video 1",
            description="",
            published_at="2026-07-01T10:00:00Z",
            channel_id="ch1",
            channel_title="Channel 1",
            subscription_id="sub1",
            activity_type="upload",
        ),
        Activity(
            video_id="vid2",
            title="Video 2",
            description="",
            published_at="2026-07-02T10:00:00Z",
            channel_id="ch2",
            channel_title="Channel 2",
            subscription_id="sub2",
            activity_type="upload",
        ),
    ]

    activities.upsert_activities(acts)

    stats = activities.get_cache_stats()
    assert stats["count"] == 2
    assert stats["oldest"] is not None
    assert stats["newest"] is not None


def test_upsert_activities_empty_list(db):
    """Test that upserting an empty list is a no-op."""
    activities.upsert_activities([])
    result = activities.get_activities()
    assert len(result) == 0





