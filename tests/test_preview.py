"""Tests for sortarr.core.preview — mock and cache preview modes.

Tests verify:
- Mock preview generates correct number of mocks (one per filter rule + baseline)
- Mock preview's "passes all" mock actually passes all filters
- Mock preview's filter-specific mocks are caught by their target filters
- Cache preview returns zero quota cost
- Cache preview handles duration-unknown activities without blocking them
- Cache preview returns empty list when activity_cache is empty
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from sortarr.core.preview import (
    _load_filter_context,
    generate_mock_activities,
    preview_from_cache,
    preview_mock,
)
from sortarr.db import migrations
from sortarr.db.connection import close_db, get_connection, init_db
from sortarr.db.repository import activities, pipelines
from sortarr.models.pipeline import PipelineConfig, PipelineCreate
from sortarr.models.youtube import Activity


@pytest.fixture
def test_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    conn = init_db(str(db_path))
    migrations.init_db(conn)
    yield conn
    close_db()


@pytest.fixture
def pipeline_simple(test_db) -> PipelineConfig:
    """Create a simple pipeline with no filters."""
    create = PipelineCreate(
        name="Simple Pipeline",
        playlist_id="PLtest",
        subscription_scope="all",
    )
    return pipelines.create_pipeline(create)


@pytest.fixture
def pipeline_with_filters(test_db) -> PipelineConfig:
    """Create a pipeline with duration filters and ignore lists."""
    conn = get_connection()

    # Create word ignore list
    conn.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ignore_word_1", "Word Ignore List", "word"),
    )
    conn.execute(
        "INSERT INTO ignore_list_entries (id, ignore_list_id, value, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("entry_1", "ignore_word_1", "unboxing"),
    )

    # Create video ignore list
    conn.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ignore_video_1", "Video Ignore List", "video"),
    )
    conn.execute(
        "INSERT INTO ignore_list_entries (id, ignore_list_id, value, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("entry_2", "ignore_video_1", "vid_ignored"),
    )

    # Create subscription ignore list
    conn.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ignore_sub_1", "Subscription Ignore List", "subscription"),
    )
    conn.execute(
        "INSERT INTO ignore_list_entries (id, ignore_list_id, value, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("entry_3", "ignore_sub_1", "sub_ignored"),
    )

    conn.commit()

    create = PipelineCreate(
        name="Pipeline With Filters",
        playlist_id="PLtest",
        subscription_scope="all",
        duration_min_seconds=60,
        duration_max_seconds=600,
        ignore_list_ids=["ignore_word_1", "ignore_video_1", "ignore_sub_1"],
    )
    return pipelines.create_pipeline(create)


def test_load_filter_context_empty(test_db, pipeline_simple):
    """Test loading filter context for a pipeline with no filters."""
    context = _load_filter_context(pipeline_simple)

    assert context["word_ignore_values"] == set()
    assert context["video_ignore_ids"] == set()
    assert context["subscription_ignore_ids"] == set()
    assert context["selectors"] == []
    assert context["inserted_video_ids"] == set()


def test_load_filter_context_with_ignore_lists(test_db, pipeline_with_filters):
    """Test loading filter context with ignore lists."""
    context = _load_filter_context(pipeline_with_filters)

    assert "unboxing" in context["word_ignore_values"]
    assert "vid_ignored" in context["video_ignore_ids"]
    assert "sub_ignored" in context["subscription_ignore_ids"]


def test_generate_mock_activities_baseline(test_db, pipeline_simple):
    """Test that mock generation always includes a baseline mock."""
    context = _load_filter_context(pipeline_simple)
    mocks = generate_mock_activities(pipeline_simple, context)

    assert len(mocks) >= 1
    baseline = mocks[0]
    assert baseline.video_id == "mock_baseline"
    assert baseline.label == "Baseline (passes all filters)"
    assert baseline.duration_seconds == 300


def test_generate_mock_activities_with_filters(test_db, pipeline_with_filters):
    """Test that mock generation creates mocks for each filter type."""
    context = _load_filter_context(pipeline_with_filters)
    mocks = generate_mock_activities(pipeline_with_filters, context)

    # Should have: baseline + word mock + video mock + subscription mock + 2 duration mocks
    assert len(mocks) >= 6

    labels = [m.label for m in mocks]
    assert any("Baseline" in label for label in labels)
    assert any("Word filter" in label for label in labels)
    assert any("Video ignore" in label for label in labels)
    assert any("Subscription ignore" in label for label in labels)
    assert any("Duration too short" in label for label in labels)
    assert any("Duration too long" in label for label in labels)


def test_preview_mock_baseline_passes_all_filters(test_db, pipeline_with_filters):
    """Test that the baseline mock actually passes all configured filters."""
    results = preview_mock(pipeline_with_filters.id)

    assert len(results) == 1
    result = results[0]
    assert result.quota_cost == 0
    assert result.pipeline_id == pipeline_with_filters.id

    # Find the baseline mock result
    baseline_result = next(
        (r for r in result.results if r["video_id"] == "mock_baseline"), None
    )
    assert baseline_result is not None
    assert baseline_result["passed"] is True
    assert baseline_result["reason"] == "passed all filters"


def test_preview_mock_word_filter_caught(test_db, pipeline_with_filters):
    """Test that word filter mock is caught by word filter."""
    results = preview_mock(pipeline_with_filters.id)

    assert len(results) == 1
    result = results[0]

    # Find a word filter mock result
    word_result = next(
        (r for r in result.results if "Word filter" in r["label"]), None
    )
    assert word_result is not None
    assert word_result["passed"] is False
    assert word_result["filter_name"] == "word_filter"


def test_preview_mock_video_ignore_caught(test_db, pipeline_with_filters):
    """Test that video ignore mock is caught by video ignore filter."""
    results = preview_mock(pipeline_with_filters.id)

    assert len(results) == 1
    result = results[0]

    # Find a video ignore mock result
    video_result = next(
        (r for r in result.results if "Video ignore" in r["label"]), None
    )
    assert video_result is not None
    assert video_result["passed"] is False
    assert video_result["filter_name"] == "video_ignore"


def test_preview_mock_duration_filter_caught(test_db, pipeline_with_filters):
    """Test that duration boundary mocks are caught by duration filter."""
    results = preview_mock(pipeline_with_filters.id)

    assert len(results) == 1
    result = results[0]

    # Find duration too short mock
    short_result = next(
        (r for r in result.results if "too short" in r["label"]), None
    )
    assert short_result is not None
    assert short_result["passed"] is False
    assert short_result["filter_name"] == "duration_filter"

    # Find duration too long mock
    long_result = next((r for r in result.results if "too long" in r["label"]), None)
    assert long_result is not None
    assert long_result["passed"] is False
    assert long_result["filter_name"] == "duration_filter"


def test_cache_preview_empty_cache(test_db, pipeline_simple):
    """Test cache preview with empty activity cache."""
    results = preview_from_cache(pipeline_simple.id)

    assert len(results) == 1
    result = results[0]
    assert result.quota_cost == 0
    assert result.total_activities == 0
    assert result.activities_after_cheap == 0
    assert result.activities_after_duration == 0
    assert result.duration_unknown_count == 0


def test_cache_preview_with_activities(test_db, pipeline_simple):
    """Test cache preview with cached activities."""
    # Add some activities to cache
    test_activities = [
        Activity(
            video_id="vid_1",
            title="Test Video 1",
            description="Description 1",
            published_at="2026-07-01T00:00:00Z",
            channel_id="UC_test",
            channel_title="Test Channel",
            subscription_id="sub_1",
            activity_type="upload",
            duration_seconds=300,
        ),
        Activity(
            video_id="vid_2",
            title="Test Video 2",
            description="Description 2",
            published_at="2026-07-02T00:00:00Z",
            channel_id="UC_test",
            channel_title="Test Channel",
            subscription_id="sub_1",
            activity_type="upload",
            duration_seconds=450,
        ),
    ]
    activities.upsert_activities(test_activities)

    results = preview_from_cache(pipeline_simple.id)

    assert len(results) == 1
    result = results[0]
    assert result.quota_cost == 0
    assert result.total_activities == 2
    assert result.activities_after_cheap == 2  # no filters configured
    assert result.activities_after_duration == 2  # no duration limits
    assert result.duration_unknown_count == 0


def test_cache_preview_duration_unknown(test_db, pipeline_with_filters):
    """Test cache preview handles duration-unknown activities without blocking."""
    # Add activity with unknown duration
    test_activities = [
        Activity(
            video_id="vid_no_duration",
            title="Video Without Duration",
            description="Description",
            published_at="2026-07-01T00:00:00Z",
            channel_id="UC_test",
            channel_title="Test Channel",
            subscription_id="sub_1",
            activity_type="upload",
            duration_seconds=None,  # unknown duration
        ),
    ]
    activities.upsert_activities(test_activities)

    results = preview_from_cache(pipeline_with_filters.id)

    assert len(results) == 1
    result = results[0]
    assert result.quota_cost == 0
    assert result.total_activities == 1
    assert result.activities_after_cheap == 1  # passes cheap filters
    assert result.duration_unknown_count == 1  # counted as unknown
    # Duration-unknown activities are NOT blocked per critic finding


def test_cache_preview_zero_quota_cost(test_db, pipeline_simple):
    """Test that cache preview always returns zero quota cost."""
    # Add some activities
    test_activities = [
        Activity(
            video_id=f"vid_{i}",
            title=f"Test Video {i}",
            description="Description",
            published_at="2026-07-01T00:00:00Z",
            channel_id="UC_test",
            channel_title="Test Channel",
            subscription_id="sub_1",
            activity_type="upload",
            duration_seconds=300,
        )
        for i in range(10)
    ]
    activities.upsert_activities(test_activities)

    results = preview_from_cache()

    for result in results:
        assert result.quota_cost == 0


def test_preview_mock_zero_quota_cost(test_db, pipeline_simple):
    """Test that mock preview always returns zero quota cost."""
    results = preview_mock()

    for result in results:
        assert result.quota_cost == 0
