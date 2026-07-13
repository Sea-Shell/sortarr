"""sortarr.core.scheduler — APScheduler cron integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

if TYPE_CHECKING:
    from apscheduler.job import Job

log = logging.getLogger("sortarr.core.scheduler")


class PipelineScheduler:
    """APScheduler integration for automated pipeline runs.

    Runs in FastAPI lifespan context. Starts on app startup, stops on shutdown.
    Reads cron schedule from app_config, triggers Runner.execute(mode='run', trigger='scheduled').
    """

    def __init__(self, cron_expression: str, run_callback: Callable[[], None]):
        """Initialize scheduler with cron schedule and callback.

        Args:
            cron_expression: Cron expression (e.g. "0 */6 * * *" for every 6 hours)
            run_callback: Callback to invoke on schedule (should trigger Runner.execute)
        """
        self.cron_expression = cron_expression
        self.run_callback = run_callback
        self.scheduler = BackgroundScheduler()
        self._job: Job | None = None

    def start(self) -> None:
        """Start scheduler and register job with cron trigger."""
        trigger = CronTrigger.from_crontab(self.cron_expression)
        self._job = self.scheduler.add_job(
            self.run_callback,
            trigger,
            id="pipeline_run",
            misfire_grace_time=3600,  # 1 hour grace for missed runs
            name="Pipeline Run",
        )
        self.scheduler.start()
        log.info(
            "scheduler started: job=%s cron=%s next_run=%s",
            self._job.id,
            self.cron_expression,
            self._job.next_run_time,
        )

    def stop(self) -> None:
        """Shutdown scheduler cleanly."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            log.info("scheduler stopped")

    def update_schedule(self, cron_expression: str) -> None:
        """Update cron schedule dynamically.

        Args:
            cron_expression: New cron expression
        """
        self.cron_expression = cron_expression
        if self._job is not None:
            trigger = CronTrigger.from_crontab(cron_expression)
            self._job.reschedule(trigger)
            log.info(
                "schedule updated: cron=%s next_run=%s",
                cron_expression,
                self._job.next_run_time,
            )

    def get_next_run_time(self) -> datetime | None:
        """Return next scheduled run time.

        Returns:
            Next run time as datetime, or None if job not scheduled
        """
        if self._job is not None:
            return self._job.next_run_time
        return None
