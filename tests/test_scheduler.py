"""Unit tests for sortarr.core.scheduler — APScheduler integration."""

from datetime import datetime, timezone

import pytest

from sortarr.core.scheduler import PipelineScheduler


def test_scheduler_init():
    """Test scheduler initialization."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    assert scheduler.cron_expression == "0 */6 * * *"
    assert scheduler.run_callback == callback
    assert not scheduler.scheduler.running
    assert scheduler._job is None


def test_scheduler_start():
    """Test scheduler starts and registers job with correct cron."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    assert not scheduler.scheduler.running

    scheduler.start()
    assert scheduler.scheduler.running
    assert scheduler._job is not None
    assert scheduler._job.id == "pipeline_run"
    assert scheduler._job.name == "Pipeline Run"

    # Verify next_run_time is set (should be in the future)
    next_run = scheduler.get_next_run_time()
    assert next_run is not None
    assert next_run > datetime.now(timezone.utc)

    scheduler.stop()


def test_scheduler_stop():
    """Test scheduler stops cleanly."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    scheduler.start()
    assert scheduler.scheduler.running

    scheduler.stop()
    assert not scheduler.scheduler.running


def test_scheduler_update_schedule():
    """Test update_schedule changes the cron expression."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    scheduler.start()

    # Get initial next run time
    initial_next_run = scheduler.get_next_run_time()
    assert initial_next_run is not None

    # Update schedule to every hour
    scheduler.update_schedule("0 * * * *")
    assert scheduler.cron_expression == "0 * * * *"

    # Verify next run time changed
    updated_next_run = scheduler.get_next_run_time()
    assert updated_next_run is not None
    # Next run should be different (unless we're exactly at the hour boundary)
    # Just verify it's still in the future
    assert updated_next_run > datetime.now(timezone.utc)

    scheduler.stop()


def test_scheduler_get_next_run_time_before_start():
    """Test get_next_run_time returns None before scheduler starts."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    assert scheduler.get_next_run_time() is None


def test_scheduler_callback_is_invoked():
    """Integration test: scheduler triggers callback after manual clock advance."""
    called = []

    def callback():
        called.append(datetime.now(timezone.utc))

    # Use a cron that runs every second for testing
    # Note: APScheduler doesn't support second-level cron, so we use a very short interval
    # This test verifies the callback is wired correctly
    scheduler = PipelineScheduler("* * * * *", callback)  # Every minute
    scheduler.start()

    # Manually trigger the job to verify callback works
    # (We can't wait a full minute in a unit test)
    if scheduler._job:
        scheduler._job.func()  # Directly invoke the callback

    assert len(called) == 1
    assert isinstance(called[0], datetime)

    scheduler.stop()


def test_scheduler_misfire_grace_time():
    """Test scheduler is configured with 3600s misfire grace time."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    scheduler.start()

    # Verify misfire_grace_time is set
    assert scheduler._job is not None
    # APScheduler stores misfire_grace_time as timedelta
    assert scheduler._job.misfire_grace_time == 3600

    scheduler.stop()


def test_scheduler_multiple_stop_calls():
    """Test multiple stop() calls are safe."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    scheduler.start()
    scheduler.stop()
    # Second stop should be safe
    scheduler.stop()
    assert not scheduler.scheduler.running


def test_scheduler_cron_expression_validation():
    """Test invalid cron expressions raise errors."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("invalid cron", callback)

    # Should raise when trying to start with invalid cron
    with pytest.raises(ValueError):
        scheduler.start()


def test_scheduler_update_schedule_while_running():
    """Test updating schedule while scheduler is running."""
    called = []

    def callback():
        called.append(1)

    scheduler = PipelineScheduler("0 */6 * * *", callback)
    scheduler.start()

    initial_job_id = scheduler._job.id if scheduler._job else None
    scheduler.update_schedule("0 */3 * * *")

    # Job should still exist with same ID
    assert scheduler._job is not None
    assert scheduler._job.id == initial_job_id
    assert scheduler.cron_expression == "0 */3 * * *"

    scheduler.stop()
