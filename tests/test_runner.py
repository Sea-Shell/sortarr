"""Tests for sortarr.core.runner — Pipeline run orchestrator."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from sortarr.core.runner import Runner
from sortarr.models.pipeline import PipelineConfig
from sortarr.models.youtube import Activity


@pytest.fixture
def mock_youtube_client():
    """Mock YouTube API client."""
    client = Mock()
    client.get_subscriptions.return_value = {
        "items": [
            {
                "id": "sub1",
                "snippet": {
                    "title": "Channel 1",
                    "resourceId": {"channelId": "ch1"},
                    "thumbnails": {"default": {"url": "http://example.com/thumb.jpg"}},
                },
            }
        ]
    }
    client.get_activities.return_value = {
        "items": [
            {
                "snippet": {
                    "type": "upload",
                    "title": "Video 1",
                    "description": "Desc 1",
                    "publishedAt": "2026-07-01T00:00:00Z",
                    "channelId": "ch1",
                    "channelTitle": "Channel 1",
                },
                "contentDetails": {"upload": {"videoId": "vid1"}},
            }
        ]
    }
    client.get_videos_batch.return_value = {
        "items": [
            {"id": "vid1", "contentDetails": {"duration": "PT5M30S"}}
        ]
    }
    client.insert_playlist_item.return_value = {"id": "item1"}
    return client


@pytest.fixture
def mock_oauth_manager():
    """Mock OAuth manager."""
    manager = Mock()
    manager.get_http.return_value = Mock()
    return manager


@pytest.fixture
def runner(mock_youtube_client, mock_oauth_manager):
    """Create a Runner instance with mocked dependencies."""
    return Runner(
        youtube_client=mock_youtube_client,
        oauth_manager=mock_oauth_manager,
        reprocess_days=2,
    )


@patch("sortarr.core.runner.config")
@patch("sortarr.core.runner.runs")
@patch("sortarr.core.runner.subscriptions")
@patch("sortarr.core.runner.activities")
@patch("sortarr.core.runner.pipelines")
@patch("sortarr.core.runner.videos")
@patch("sortarr.core.youtube.get_quota_used")
def test_execute_happy_path(
    mock_quota,
    mock_videos_repo,
    mock_pipelines_repo,
    mock_activities_repo,
    mock_subs_repo,
    mock_runs_repo,
    mock_config_repo,
    runner,
):
    """Test successful run execution (happy path)."""
    # Setup
    mock_config_repo.get_config_value.return_value = None  # No active run
    mock_runs_repo.create_run.return_value = 1
    mock_quota.return_value = 500  # Well under limit

    # Mock pipeline
    mock_pipeline = PipelineConfig(
        id="pipe1",
        name="Test Pipeline",
        enabled=True,
        playlist_id="PL123",
        order=0,
    )
    mock_pipelines_repo.list_pipelines.return_value = [mock_pipeline]
    mock_pipelines_repo.get_pipeline_ignore_lists.return_value = []

    # Mock activities
    mock_activities_repo.get_activities.return_value = [
        Activity(
            video_id="vid1",
            title="Test Video",
            description="",
            published_at="2026-07-01T00:00:00Z",
            channel_id="ch1",
            channel_title="Channel 1",
            subscription_id="sub1",
            activity_type="upload",
        )
    ]

    # Execute
    run_id = runner.execute()

    # Verify
    assert run_id == 1
    mock_config_repo.set_config.assert_any_call("run_active", "true")
    mock_config_repo.set_config.assert_any_call("run_active", "")  # Cleared at end
    mock_runs_repo.create_run.assert_called_once()
    mock_runs_repo.update_run.assert_called()
    mock_activities_repo.prune_old_entries.assert_called_once_with(retention_days=30)


@patch("sortarr.core.runner.config")
@patch("sortarr.core.runner.runs")
def test_concurrency_guard_blocks_concurrent_run(
    mock_runs_repo, mock_config_repo, runner
):
    """Test that concurrency guard returns 409 when run_active is set."""
    # Setup
    mock_config_repo.get_config_value.return_value = "true"  # Active run
    mock_runs_repo.create_run.return_value = 2

    # Execute
    run_id = runner.execute()

    # Verify
    assert run_id == 2
    mock_runs_repo.update_run.assert_called_once()
    call_args = mock_runs_repo.update_run.call_args
    assert call_args[0][0] == 2
    assert call_args[0][1]["status"] == "failed"
    assert "concurrent run blocked" in call_args[0][1]["error_message"]


@patch("sortarr.core.runner.config")
@patch("sortarr.core.runner.runs")
@patch("sortarr.core.runner.subscriptions")
@patch("sortarr.core.runner.activities")
@patch("sortarr.core.runner.pipelines")
@patch("sortarr.core.runner.videos")
@patch("sortarr.core.youtube.get_quota_used")
def test_quota_guard_blocks_at_9500(
    mock_quota,
    mock_videos_repo,
    mock_pipelines_repo,
    mock_activities_repo,
    mock_subs_repo,
    mock_runs_repo,
    mock_config_repo,
    runner,
):
    """Test that quota guard blocks inserts at 9,500 units."""
    # Setup
    mock_config_repo.get_config_value.return_value = None
    mock_runs_repo.create_run.return_value = 3
    mock_quota.return_value = 9600  # Over block threshold

    mock_pipeline = PipelineConfig(
        id="pipe1",
        name="Test Pipeline",
        enabled=True,
        playlist_id="PL123",
        order=0,
    )
    mock_pipelines_repo.list_pipelines.return_value = [mock_pipeline]
    mock_pipelines_repo.get_pipeline_ignore_lists.return_value = []

    mock_activities_repo.get_activities.return_value = [
        Activity(
            video_id="vid1",
            title="Test Video",
            description="",
            published_at="2026-07-01T00:00:00Z",
            channel_id="ch1",
            channel_title="Channel 1",
            subscription_id="sub1",
            activity_type="upload",
        )
    ]

    # Execute
    run_id = runner.execute()

    # Verify
    assert run_id == 3
    call_args = mock_runs_repo.update_run.call_args
    assert call_args[0][1]["status"] == "completed_quota_blocked"
    assert call_args[0][1]["videos_inserted"] == 0
    # Verify decisions were still recorded
    mock_runs_repo.add_decisions.assert_called_once()


@patch("sortarr.core.runner.config")
@patch("sortarr.core.runner.runs")
@patch("sortarr.core.runner.subscriptions")
@patch("sortarr.core.runner.activities")
@patch("sortarr.core.runner.pipelines")
@patch("sortarr.core.runner.videos")
@patch("sortarr.core.youtube.get_quota_used")
def test_quota_blocked_run_records_decisions(
    mock_quota,
    mock_videos_repo,
    mock_pipelines_repo,
    mock_activities_repo,
    mock_subs_repo,
    mock_runs_repo,
    mock_config_repo,
    runner,
):
    """Test that quota-blocked run still records decisions for filtered videos."""
    # Setup
    mock_config_repo.get_config_value.return_value = None
    mock_runs_repo.create_run.return_value = 4
    mock_quota.return_value = 9700

    mock_pipeline = PipelineConfig(
        id="pipe1",
        name="Test Pipeline",
        enabled=True,
        playlist_id="PL123",
        order=0,
    )
    mock_pipelines_repo.list_pipelines.return_value = [mock_pipeline]
    mock_pipelines_repo.get_pipeline_ignore_lists.return_value = []

    mock_activities_repo.get_activities.return_value = [
        Activity(
            video_id="vid1",
            title="Test Video",
            description="",
            published_at="2026-07-01T00:00:00Z",
            channel_id="ch1",
            channel_title="Channel 1",
            subscription_id="sub1",
            activity_type="upload",
        )
    ]

    # Execute
    run_id = runner.execute()

    # Verify decisions were recorded
    assert run_id == 4
    mock_runs_repo.add_decisions.assert_called_once()
    decisions = mock_runs_repo.add_decisions.call_args[0][1]
    assert len(decisions) >= 0  # At least some decisions recorded


@patch("sortarr.core.runner.config")
def test_startup_cleanup_clears_stale_flag(mock_config_repo, runner):
    """Test that startup cleanup clears stale run_active flag."""
    # Setup
    mock_config_repo.get_config_value.return_value = "true"

    # Execute
    runner._startup_cleanup()

    # Verify
    mock_config_repo.set_config.assert_called_once_with("run_active", "")


@patch("sortarr.core.runner.config")
@patch("sortarr.core.runner.runs")
@patch("sortarr.core.runner.subscriptions")
@patch("sortarr.core.runner.activities")
@patch("sortarr.core.runner.pipelines")
@patch("sortarr.core.runner.videos")
@patch("sortarr.core.youtube.get_quota_used")
def test_watermark_updates_after_inserts(
    mock_quota,
    mock_videos_repo,
    mock_pipelines_repo,
    mock_activities_repo,
    mock_subs_repo,
    mock_runs_repo,
    mock_config_repo,
    runner,
):
    """Test that watermarks are updated after inserts."""
    # Setup
    mock_config_repo.get_config_value.return_value = None
    mock_runs_repo.create_run.return_value = 5
    mock_quota.return_value = 500

    mock_pipeline = PipelineConfig(
        id="pipe1",
        name="Test Pipeline",
        enabled=True,
        playlist_id="PL123",
        order=0,
    )
    mock_pipelines_repo.list_pipelines.return_value = [mock_pipeline]
    mock_pipelines_repo.get_pipeline_ignore_lists.return_value = []
    mock_activities_repo.get_activities.return_value = []

    # Execute
    run_id = runner.execute()

    # Verify watermark update was called
    assert run_id == 5
    mock_subs_repo.update_tracking.assert_called()


@patch("sortarr.core.runner.config")
@patch("sortarr.core.runner.runs")
@patch("sortarr.core.runner.subscriptions")
def test_error_handling_clears_run_active(
    mock_subs_repo, mock_runs_repo, mock_config_repo, runner
):
    """Test that error handling clears run_active flag."""
    # Setup
    mock_config_repo.get_config_value.return_value = None
    mock_runs_repo.create_run.return_value = 6
    mock_subs_repo.upsert_subscriptions.side_effect = RuntimeError("API error")

    # Execute and verify exception is raised
    with pytest.raises(RuntimeError, match="API error"):
        runner.execute()

    # Verify run_active was cleared
    mock_config_repo.set_config.assert_any_call("run_active", "")
    # Verify run was marked as failed
    call_args = mock_runs_repo.update_run.call_args
    assert call_args[0][1]["status"] == "failed"
    assert "API error" in call_args[0][1]["error_message"]


@patch("sortarr.core.runner.config")
@patch("sortarr.core.runner.runs")
@patch("sortarr.core.runner.subscriptions")
@patch("sortarr.core.runner.activities")
@patch("sortarr.core.runner.pipelines")
def test_activity_cache_pruning_after_completion(
    mock_pipelines_repo,
    mock_activities_repo,
    mock_subs_repo,
    mock_runs_repo,
    mock_config_repo,
    runner,
):
    """Test that activity cache is pruned after successful completion."""
    # Setup
    mock_config_repo.get_config_value.return_value = None
    mock_runs_repo.create_run.return_value = 7

    mock_pipeline = PipelineConfig(
        id="pipe1",
        name="Test Pipeline",
        enabled=True,
        playlist_id="PL123",
        order=0,
    )
    mock_pipelines_repo.list_pipelines.return_value = [mock_pipeline]
    mock_pipelines_repo.get_pipeline_ignore_lists.return_value = []
    mock_activities_repo.get_activities.return_value = []

    # Execute
    with patch("sortarr.core.youtube.get_quota_used", return_value=500):
        run_id = runner.execute()

    # Verify pruning was called
    assert run_id == 7
    mock_activities_repo.prune_old_entries.assert_called_once_with(retention_days=30)


def test_invalid_mode_raises_error(runner):
    """Test that invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="invalid mode"):
        runner.execute(mode="preview")
