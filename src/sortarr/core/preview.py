"""sortarr.core.preview — Mock and cache preview modes.

Separated from run logic per design gate requirement.
Zero YouTube API calls for both modes.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sortarr.core.filters import FilterChain
from sortarr.db.connection import get_connection
from sortarr.db.repository import activities, pipelines
from sortarr.models.pipeline import (
    CachePreviewResponse,
    MockActivity,
    MockPreviewResponse,
    PipelineConfig,
)

log = logging.getLogger("sortarr.core.preview")


def _load_filter_context(pipeline: PipelineConfig) -> dict:
    """Load filter context for a pipeline.

    Builds the context dict expected by filter functions:
    - word_ignore_values: set of lowercase words from word-type ignore lists
    - video_ignore_ids: set of video IDs from video-type ignore lists
    - subscription_ignore_ids: set of subscription IDs from subscription-type ignore lists
    - selectors: list of selector dicts with field/operator/pattern
    - inserted_video_ids: set of already-inserted video IDs
    """
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


def generate_mock_activities(
    pipeline: PipelineConfig, context: dict
) -> list[MockActivity]:
    """Generate deterministic test activities for a pipeline.

    Creates one mock per configured filter rule to exercise each filter independently,
    plus a baseline "passes all" mock.

    Returns activities with descriptive labels.
    """
    mocks: list[MockActivity] = []
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    # Baseline: passes all filters
    mocks.append(
        MockActivity(
            video_id="mock_baseline",
            title="Baseline Video Title",
            description="This mock should pass all configured filters",
            channel_id="UCbaseline",
            channel_title="Baseline Channel",
            subscription_id="sub_baseline",
            published_at=now,
            activity_type="upload",
            duration_seconds=300,  # 5 minutes
            label="Baseline (passes all filters)",
        )
    )

    # Word filter mocks — one per word in word ignore list
    word_ignore_values = context.get("word_ignore_values", set())
    for word in list(word_ignore_values)[:3]:  # limit to first 3 for brevity
        mocks.append(
            MockActivity(
                video_id=f"mock_word_{word[:10]}",
                title=f"Video with {word} in title",
                description="Mock for word filter",
                channel_id="UCword",
                channel_title="Word Filter Test Channel",
                subscription_id="sub_word",
                published_at=now,
                activity_type="upload",
                duration_seconds=300,
                label=f"Word filter: '{word}'",
            )
        )

    # Video ignore mocks — one per video in video ignore list
    video_ignore_ids = context.get("video_ignore_ids", set())
    for video_id in list(video_ignore_ids)[:3]:  # limit to first 3
        mocks.append(
            MockActivity(
                video_id=video_id,
                title="Ignored Video",
                description="Mock for video ignore filter",
                channel_id="UCvideo",
                channel_title="Video Ignore Test Channel",
                subscription_id="sub_video",
                published_at=now,
                activity_type="upload",
                duration_seconds=300,
                label=f"Video ignore: {video_id}",
            )
        )

    # Subscription ignore mocks — one per subscription in subscription ignore list
    subscription_ignore_ids = context.get("subscription_ignore_ids", set())
    for sub_id in list(subscription_ignore_ids)[:3]:  # limit to first 3
        mocks.append(
            MockActivity(
                video_id=f"mock_sub_{sub_id[:10]}",
                title="Subscription Ignored Video",
                description="Mock for subscription ignore filter",
                channel_id="UCsub",
                channel_title="Subscription Ignore Test Channel",
                subscription_id=sub_id,
                published_at=now,
                activity_type="upload",
                duration_seconds=300,
                label=f"Subscription ignore: {sub_id}",
            )
        )

    # Duration boundary mocks
    if pipeline.duration_min_seconds is not None and pipeline.duration_min_seconds > 0:
        mocks.append(
            MockActivity(
                video_id="mock_duration_too_short",
                title="Too Short Video",
                description="Mock for duration min boundary",
                channel_id="UCduration",
                channel_title="Duration Test Channel",
                subscription_id="sub_duration",
                published_at=now,
                activity_type="upload",
                duration_seconds=max(1, pipeline.duration_min_seconds - 10),
                label=f"Duration too short (< {pipeline.duration_min_seconds}s)",
            )
        )

    if pipeline.duration_max_seconds is not None and pipeline.duration_max_seconds > 0:
        mocks.append(
            MockActivity(
                video_id="mock_duration_too_long",
                title="Too Long Video",
                description="Mock for duration max boundary",
                channel_id="UCduration",
                channel_title="Duration Test Channel",
                subscription_id="sub_duration",
                published_at=now,
                activity_type="upload",
                duration_seconds=pipeline.duration_max_seconds + 100,
                label=f"Duration too long (> {pipeline.duration_max_seconds}s)",
            )
        )

    return mocks


def preview_mock(pipeline_id: str | None = None) -> list[MockPreviewResponse]:
    """Run mock preview for one or all pipelines.

    Generates synthetic test activities and runs them through the filter chain.
    Zero API calls, zero quota cost.
    """
    pipeline_list = pipelines.list_pipelines()
    if pipeline_id:
        pipeline_list = [p for p in pipeline_list if p.id == pipeline_id]
    pipeline_list = [p for p in pipeline_list if p.enabled]

    results: list[MockPreviewResponse] = []

    for pipeline_resp in pipeline_list:
        # Convert PipelineResponse to PipelineConfig
        pipeline = PipelineConfig(
            id=pipeline_resp.id,
            name=pipeline_resp.name,
            enabled=pipeline_resp.enabled,
            playlist_id=pipeline_resp.playlist_id,
            order=pipeline_resp.order,
            subscription_scope=pipeline_resp.subscription_scope,
            duration_min_seconds=pipeline_resp.duration_min_seconds,
            duration_max_seconds=pipeline_resp.duration_max_seconds,
            selector_mode=pipeline_resp.selector_mode,
        )

        context = _load_filter_context(pipeline)
        mocks = generate_mock_activities(pipeline, context)
        chain = FilterChain(pipeline, context)

        filter_results = []
        for mock in mocks:
            activity_dict = mock.model_dump()

            # Run cheap filters
            result = chain.run_cheap_filters(activity_dict)
            if result is None:
                # Passed cheap filters — run duration filter
                duration_map = {mock.video_id: mock.duration_seconds or 0}
                result = chain.run_duration_filter(activity_dict, duration_map)

            filter_results.append(
                {
                    "video_id": mock.video_id,
                    "label": mock.label,
                    "passed": result is None,
                    "filter_stage": result.filter_stage if result else None,
                    "filter_name": result.filter_name if result else None,
                    "reason": result.reason if result else "passed all filters",
                }
            )

        results.append(
            MockPreviewResponse(
                pipeline_id=pipeline.id,
                pipeline_name=pipeline.name,
                activities=mocks,
                results=filter_results,
                quota_cost=0,
            )
        )

    return results


def preview_from_cache(pipeline_id: str | None = None) -> list[CachePreviewResponse]:
    """Run cache preview for one or all pipelines.

    Reads from persistent activity_cache and applies full filter chain.
    Zero API calls, zero quota cost.

    Duration-unknown activities are counted but NOT blocked (per critic finding).
    """
    pipeline_list = pipelines.list_pipelines()
    if pipeline_id:
        pipeline_list = [p for p in pipeline_list if p.id == pipeline_id]
    pipeline_list = [p for p in pipeline_list if p.enabled]

    # Load working set from cache
    working_set = activities.get_activities()

    results: list[CachePreviewResponse] = []

    for pipeline_resp in pipeline_list:
        # Convert PipelineResponse to PipelineConfig
        pipeline = PipelineConfig(
            id=pipeline_resp.id,
            name=pipeline_resp.name,
            enabled=pipeline_resp.enabled,
            playlist_id=pipeline_resp.playlist_id,
            order=pipeline_resp.order,
            subscription_scope=pipeline_resp.subscription_scope,
            duration_min_seconds=pipeline_resp.duration_min_seconds,
            duration_max_seconds=pipeline_resp.duration_max_seconds,
            selector_mode=pipeline_resp.selector_mode,
        )

        context = _load_filter_context(pipeline)
        chain = FilterChain(pipeline, context)

        total_activities = len(working_set)
        activities_after_cheap = 0
        activities_after_duration = 0
        duration_unknown_count = 0

        survivors_after_cheap = []

        # Run cheap filters
        for activity in working_set:
            activity_dict = activity.model_dump()
            result = chain.run_cheap_filters(activity_dict)
            if result is None:
                survivors_after_cheap.append(activity)

        activities_after_cheap = len(survivors_after_cheap)

        # Build duration map from cached durations
        duration_map = {}
        for activity in survivors_after_cheap:
            if activity.duration_seconds is not None:
                duration_map[activity.video_id] = activity.duration_seconds
            else:
                duration_unknown_count += 1

        # Run duration filters
        for activity in survivors_after_cheap:
            activity_dict = activity.model_dump()
            result = chain.run_duration_filter(activity_dict, duration_map)
            if result is None:
                activities_after_duration += 1

        results.append(
            CachePreviewResponse(
                pipeline_id=pipeline.id,
                pipeline_name=pipeline.name,
                total_activities=total_activities,
                activities_after_cheap=activities_after_cheap,
                activities_after_duration=activities_after_duration,
                duration_unknown_count=duration_unknown_count,
                quota_cost=0,
            )
        )

    return results
