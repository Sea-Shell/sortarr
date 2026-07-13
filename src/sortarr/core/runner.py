"""
sortarr.core.runner — Pipeline run orchestrator.

Executes the 8-step flow:
1. Startup cleanup (clear stale run_active flag)
2. Create pipeline_run record (status=running)
3. Concurrency guard (check run_active, set if clear)
4. Fetch subscriptions (YouTube API)
5. For each subscription: fetch activities → upsert to activity_cache
6. Load working set from activity_cache
7. For each pipeline: run cheap filters → survivors
8. Deduplicate survivor video IDs across pipelines
9. Batch videos.list for unique IDs → shared duration map
10. Update activity_cache.duration_seconds
11. For each pipeline: run duration filters
12. For each pipeline: insert survivors into playlist
13. Update watermarks in subscription_tracking
14. Record run summary (status=completed)
15. Clear run_active
16. Prune activity cache (30-day retention)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sortarr.core.enricher import Enricher
from sortarr.core.filters import FilterChain
from sortarr.db.repository import activities, config, pipelines, runs, subscriptions, videos
from sortarr.metrics import (
    sortarr_quota_used_today,
    sortarr_run_duration_seconds,
    sortarr_runs_total,
    sortarr_videos_inserted_total,
)
from sortarr.models.pipeline import RunSummary
from sortarr.models.youtube import Activity, Subscription, Video

if TYPE_CHECKING:
    from google.auth.transport.requests import AuthorizedSession

    from sortarr.core.auth import OAuthManager
    from sortarr.core.youtube import YouTubeAPIClient

log = logging.getLogger("sortarr.core.runner")

# Quota limits
QUOTA_WARN_THRESHOLD = 8000  # 80%
QUOTA_BLOCK_THRESHOLD = 9500  # 95%
DAILY_QUOTA_LIMIT = 10000


class Runner:
    """Pipeline run orchestrator."""

    def __init__(
        self,
        youtube_client: YouTubeAPIClient,
        oauth_manager: OAuthManager,
        reprocess_days: int = 2,
        activity_limit: int = 0,
        subscription_limit: int = 0,
        published_after: str | None = None,
    ):
        self.youtube_client = youtube_client
        self.oauth_manager = oauth_manager
        self.reprocess_days = reprocess_days
        self.activity_limit = activity_limit
        self.subscription_limit = subscription_limit
        self.published_after = published_after

    def execute(self, mode: str = "run", pipeline_id: str | None = None) -> int:
        """Execute a pipeline run.

        mode: "run" (live run with API calls)
        pipeline_id: Optional pipeline ID to run (None = all enabled)

        Returns: run_id
        """
        if mode != "run":
            raise ValueError(f"invalid mode: {mode} (only 'run' supported in T4.1)")

        # Record run start time for duration metric
        import time
        start_time = time.time()

        # Step 0: Startup cleanup (crash recovery)
        self._startup_cleanup()

        # Step 1: Create run record
        run_summary = RunSummary(
            status="running",
            trigger="manual",  # TODO: detect scheduled vs manual
            started_at=datetime.now(UTC).isoformat(),
        )
        run_id = runs.create_run(run_summary)
        log.info("started run %d", run_id)

        try:
            # Step 2: Concurrency guard (atomic check-and-set)
            from sortarr.db.connection import get_connection
            import sqlite3

            try:
                conn = get_connection()
                conn.execute(
                    "INSERT INTO app_config (key, value) VALUES ('run_active', 'true')"
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Another run is active
                log.warning("run already active — returning 409")
                runs.update_run(
                    run_id,
                    {
                        "status": "failed",
                        "finished_at": datetime.now(UTC).isoformat(),
                        "error_message": "concurrent run blocked",
                    },
                )
                return run_id

            # Step 3: Fetch subscriptions
            http = self.oauth_manager.get_http()
            subs = self._fetch_all_subscriptions(http)
            subscriptions.upsert_subscriptions(subs)
            run_summary.subscriptions_fetched = len(subs)
            log.info("fetched %d subscriptions", len(subs))

            # Step 4: Fetch activities for each subscription
            all_activities = []
            subs_to_fetch = (
                subs[: self.subscription_limit] if self.subscription_limit else subs
            )
            for sub in subs_to_fetch:
                tracking = subscriptions.get_tracking(sub.subscription_id)
                published_after = (
                    self.published_after
                    or (tracking.get("last_fetched_at") if tracking else None)
                )
                if not published_after:
                    # Default: reprocess_days back
                    published_after = (
                        datetime.now(UTC) - timedelta(days=self.reprocess_days)
                    ).isoformat() + "Z"

                acts = self._fetch_activities_for_subscription(
                    http, sub.channel_id, published_after
                )
                all_activities.extend(acts)

            activities.upsert_activities(all_activities)
            run_summary.activities_collected = len(all_activities)
            log.info("collected %d activities", len(all_activities))

            # Step 5: Load working set from cache
            working_set = activities.get_activities()

            # Step 6: Load pipelines
            pipeline_list = pipelines.list_pipelines()
            if pipeline_id:
                pipeline_list = [p for p in pipeline_list if p.id == pipeline_id]
            # Convert PipelineResponse to PipelineConfig for filter chain
            from sortarr.models.pipeline import PipelineConfig

            pipeline_configs = [
                PipelineConfig(
                    id=p.id,
                    name=p.name,
                    enabled=p.enabled,
                    playlist_id=p.playlist_id,
                    order=p.order,
                    subscription_scope=p.subscription_scope,
                    duration_min_seconds=p.duration_min_seconds,
                    duration_max_seconds=p.duration_max_seconds,
                    selector_mode=p.selector_mode,
                )
                for p in pipeline_list
                if p.enabled
            ]

            # Step 7: Run cheap filters per pipeline
            survivors_per_pipeline: dict[str, list[Activity]] = {}
            decisions: list[dict] = []

            for pipeline in pipeline_configs:
                chain = FilterChain(pipeline, self._build_filter_context(pipeline))
                survivors: list[Activity] = []

                for activity in working_set:
                    result = chain.run_cheap_filters(activity.model_dump())
                    if result is None:
                        # Passed all cheap filters
                        survivors.append(activity)
                    else:
                        # Failed a filter
                        decisions.append(
                            {
                                "pipeline_id": pipeline.id,
                                "video_id": activity.video_id,
                                "action": "skipped",
                                "filter_stage": "cheap",
                                "filter_name": result.filter_name,
                                "reason": result.reason,
                            }
                        )

                survivors_per_pipeline[pipeline.id] = survivors

            # Step 8: Deduplicate survivor video IDs
            unique_video_ids: set[str] = set()
            for survivors in survivors_per_pipeline.values():
                for activity in survivors:
                    unique_video_ids.add(activity.video_id)

            # Step 9: Batch enrich durations
            enricher = Enricher(
                lambda ids_csv: self.youtube_client.get_videos_batch(http, ids_csv)
            )
            duration_map, failed_ids = enricher.batch_fetch(unique_video_ids)
            run_summary.videos_enriched = len(duration_map)
            
            if failed_ids:
                log.warning("failed to enrich %d videos: %s", len(failed_ids), failed_ids[:10])

            # Update activity_cache with durations
            for video_id, duration in duration_map.items():
                activities.update_duration(video_id, duration)

            # Step 10: Check quota before inserts
            from sortarr.core.youtube import get_quota_used

            quota_used = get_quota_used()

            if quota_used >= QUOTA_WARN_THRESHOLD:
                log.warning(
                    "quota usage at %d/%d (%.1f%%) — approaching limit",
                    quota_used,
                    DAILY_QUOTA_LIMIT,
                    quota_used / DAILY_QUOTA_LIMIT * 100,
                )

            if quota_used >= QUOTA_BLOCK_THRESHOLD:
                log.error(
                    "quota limit reached (%d/%d) — run completed without inserts",
                    quota_used,
                    DAILY_QUOTA_LIMIT,
                )
                runs.update_run(
                    run_id,
                    {
                        "status": "completed_quota_blocked",
                        "finished_at": datetime.now(UTC).isoformat(),
                        "subscriptions_processed": run_summary.subscriptions_fetched,
                        "videos_collected": run_summary.activities_collected,
                        "videos_after_cheap_filters": len(unique_video_ids),
                        "videos_inserted": 0,
                        "quota_used": quota_used,
                    },
                )
                runs.add_decisions(run_id, decisions)
                conn = get_connection()
                conn.execute("DELETE FROM app_config WHERE key = 'run_active'")
                conn.commit()
                
                # Record metrics for quota-blocked run
                duration = time.time() - start_time
                sortarr_runs_total.labels(trigger=run_summary.trigger).inc()
                sortarr_quota_used_today.set(quota_used)
                sortarr_run_duration_seconds.observe(duration)
                
                return run_id

            # Step 11: Run duration filters and insert
            for pipeline in pipeline_configs:
                survivors = survivors_per_pipeline[pipeline.id]
                
                # Defensive check: skip pipeline if no playlist_id
                if not pipeline.playlist_id:
                    log.error("pipeline %s has no playlist_id — skipping inserts", pipeline.id)
                    run_summary.videos_skipped += len(survivors)
                    continue

                for activity in survivors:
                    # Run duration filter
                    chain = FilterChain(pipeline, {"duration_map": duration_map})
                    result = chain.run_duration_filter(
                        activity.model_dump(), duration_map
                    )

                    if result is None:
                        # Passed duration filter — insert
                        self.youtube_client.insert_playlist_item(
                            http, pipeline.playlist_id or "", activity.video_id
                        )
                        videos.insert_video(
                            Video(
                                video_id=activity.video_id,
                                title=activity.title,
                                channel_id=activity.channel_id,
                                channel_title=activity.channel_title,
                                published_at=activity.published_at,
                                duration_seconds=duration_map.get(activity.video_id),
                                pipeline_id=pipeline.id,
                                playlist_id=pipeline.playlist_id,
                            )
                        )
                        run_summary.videos_inserted += 1

                        decisions.append(
                            {
                                "pipeline_id": pipeline.id,
                                "video_id": activity.video_id,
                                "action": "inserted",
                                "filter_stage": None,
                                "filter_name": None,
                                "reason": None,
                            }
                        )
                    else:
                        # Failed duration filter
                        run_summary.videos_skipped += 1
                        decisions.append(
                            {
                                "pipeline_id": pipeline.id,
                                "video_id": activity.video_id,
                                "action": "skipped",
                                "filter_stage": "duration",
                                "filter_name": result.filter_name,
                                "reason": result.reason,
                            }
                        )

            # Step 12: Update watermarks
            for sub in subs:
                subscriptions.update_tracking(
                    sub.subscription_id, datetime.now(UTC).isoformat()
                )

            # Step 13: Record run summary
            final_quota = get_quota_used()
            runs.update_run(
                run_id,
                {
                    "status": "completed",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "subscriptions_processed": run_summary.subscriptions_fetched,
                    "videos_collected": run_summary.activities_collected,
                    "videos_after_cheap_filters": len(unique_video_ids),
                    "videos_inserted": run_summary.videos_inserted,
                    "quota_used": final_quota,
                },
            )
            runs.add_decisions(run_id, decisions)

            # Step 14: Clear run_active
            conn = get_connection()
            conn.execute("DELETE FROM app_config WHERE key = 'run_active'")
            conn.commit()

            # Step 15: Prune activity cache
            activities.prune_old_entries(retention_days=30)

            # Record Prometheus metrics
            duration = time.time() - start_time
            sortarr_runs_total.labels(trigger=run_summary.trigger).inc()
            sortarr_videos_inserted_total.inc(run_summary.videos_inserted)
            sortarr_quota_used_today.set(final_quota)
            sortarr_run_duration_seconds.observe(duration)

            log.info(
                "run %d completed: %d inserted, %d skipped",
                run_id,
                run_summary.videos_inserted,
                run_summary.videos_skipped,
            )
            return run_id

        except Exception as e:
            log.exception("run %d failed: %s", run_id, e)
            runs.update_run(
                run_id,
                {
                    "status": "failed",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "error_message": str(e),
                },
            )
            conn = get_connection()
            conn.execute("DELETE FROM app_config WHERE key = 'run_active'")
            conn.commit()
            raise

    def _startup_cleanup(self) -> None:
        """Clear stale run_active flag on startup (crash recovery)."""
        from sortarr.db.connection import get_connection

        if config.get_config_value("run_active"):
            log.warning("clearing stale run_active flag from previous crashed run")
            conn = get_connection()
            conn.execute("DELETE FROM app_config WHERE key = 'run_active'")
            conn.commit()

    def _fetch_all_subscriptions(
        self, http: AuthorizedSession
    ) -> list[Subscription]:
        """Fetch all subscriptions with pagination."""
        subs: list[Subscription] = []
        page_token: str | None = None

        while True:
            response = self.youtube_client.get_subscriptions(
                http, page_token=page_token
            )
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                subs.append(
                    Subscription(
                        subscription_id=item.get("id", ""),
                        channel_id=snippet.get("resourceId", {}).get("channelId", ""),
                        channel_title=snippet.get("title", ""),
                        thumbnail_url=snippet.get("thumbnails", {})
                        .get("default", {})
                        .get("url"),
                    )
                )

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return subs

    def _fetch_activities_for_subscription(
        self, http: AuthorizedSession, channel_id: str, published_after: str
    ) -> list[Activity]:
        """Fetch activities for a subscription with pagination."""
        acts: list[Activity] = []
        page_token: str | None = None

        while True:
            response = self.youtube_client.get_activities(
                http, channel_id, published_after, page_token=page_token
            )
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})

                # Only process upload activities
                if snippet.get("type") != "upload":
                    continue

                video_id = content_details.get("upload", {}).get("videoId")
                if not video_id:
                    continue

                acts.append(
                    Activity(
                        video_id=video_id,
                        title=snippet.get("title", ""),
                        description=snippet.get("description", ""),
                        published_at=snippet.get("publishedAt", ""),
                        channel_id=snippet.get("channelId", ""),
                        channel_title=snippet.get("channelTitle", ""),
                        subscription_id=channel_id,  # Use channel_id as subscription_id
                        activity_type="upload",
                    )
                )

            page_token = response.get("nextPageToken")
            if not page_token or (
                self.activity_limit and len(acts) >= self.activity_limit
            ):
                break

        return acts[: self.activity_limit] if self.activity_limit else acts

    def _build_filter_context(self, pipeline) -> dict:
        """Build context dict for filter chain.

        Builds the context dict expected by filter functions:
        - word_ignore_values: set of lowercase words from word-type ignore lists
        - video_ignore_ids: set of video IDs from video-type ignore lists
        - subscription_ignore_ids: set of subscription IDs from subscription-type ignore lists
        - selectors: list of selector dicts with field/operator/pattern
        - inserted_video_ids: set of already-inserted video IDs
        """
        from sortarr.db.connection import get_connection

        conn = get_connection()
        context: dict = {
            "word_ignore_values": set(),
            "video_ignore_ids": set(),
            "subscription_ignore_ids": set(),
            "selectors": [],
            "inserted_video_ids": set(),
        }

        # Load ignore list entries for this pipeline
        ignore_list_ids = pipelines.get_pipeline_ignore_lists(pipeline.id)
        if ignore_list_ids:
            placeholders = ",".join("?" * len(ignore_list_ids))
            rows = conn.execute(
                f"""
                SELECT il.list_type, ile.value
                FROM ignore_lists il
                JOIN ignore_list_entries ile ON ile.ignore_list_id = il.id
                WHERE il.id IN ({placeholders})
            """,
                ignore_list_ids,
            ).fetchall()

            for row in rows:
                list_type = row["list_type"]
                value = row["value"]
                if list_type == "word":
                    context["word_ignore_values"].add(value.lower())
                elif list_type == "video":
                    context["video_ignore_ids"].add(value)
                elif list_type == "subscription":
                    context["subscription_ignore_ids"].add(value)

        # Load selectors for this pipeline
        selector_ids = pipelines.get_pipeline_selectors(pipeline.id)
        if selector_ids:
            placeholders = ",".join("?" * len(selector_ids))
            rows = conn.execute(
                f"""
                SELECT field, operator, pattern, combine_operator
                FROM pipeline_selectors
                WHERE id IN ({placeholders})
            """,
                selector_ids,
            ).fetchall()

            context["selectors"] = [
                {
                    "field": row["field"],
                    "operator": row["operator"],
                    "pattern": row["pattern"],
                    "combine_operator": row["combine_operator"],
                }
                for row in rows
            ]

        # Load already-inserted video IDs
        rows = conn.execute("SELECT video_id FROM videos").fetchall()
        context["inserted_video_ids"] = {row["video_id"] for row in rows}

        return context

