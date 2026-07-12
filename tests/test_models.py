"""Tests for sortarr v2 Pydantic models and Settings."""

from __future__ import annotations

import json

import pytest

from sortarr.config import Settings, load_settings
from sortarr.models.pipeline import (
    CachePreviewResponse,
    FilterResult,
    FilterStage,
    MockActivity,
    MockPreviewResponse,
    PipelineConfig,
    PipelineCreate,
    PipelineResponse,
    PipelineUpdate,
    PreviewRequest,
    RunDecisionResponse,
    RunSummary,
    RunSummaryResponse,
)
from sortarr.models.youtube import (
    Activity,
    ConfigResponse,
    ConfigUpdate,
    HealthResponse,
    Subscription,
    Video,
)


# ── FilterStage enum ──


class TestFilterStage:
    def test_values(self) -> None:
        assert FilterStage.CHEAP == "cheap"
        assert FilterStage.DURATION == "duration"

    def test_str_enum(self) -> None:
        assert isinstance(FilterStage.CHEAP, str)


# ── FilterResult ──


class TestFilterResult:
    def test_basic(self) -> None:
        r = FilterResult(
            filter_stage=FilterStage.CHEAP,
            filter_name="word_filter",
            passed=False,
            reason="title blocked",
        )
        assert r.passed is False
        assert r.filter_stage == FilterStage.CHEAP

    def test_roundtrip(self) -> None:
        r = FilterResult(
            filter_stage=FilterStage.DURATION,
            filter_name="min_duration",
            passed=True,
        )
        data = r.model_dump()
        r2 = FilterResult.model_validate(data)
        assert r == r2

    def test_reason_optional(self) -> None:
        r = FilterResult(
            filter_stage=FilterStage.CHEAP,
            filter_name="db_exists",
            passed=True,
        )
        assert r.reason is None


# ── PipelineConfig ──


class TestPipelineConfig:
    def test_defaults(self) -> None:
        pc = PipelineConfig(name="Test Pipeline")
        assert pc.enabled is True
        assert pc.order == 0
        assert pc.subscription_scope == "all"
        assert pc.selector_mode == "AND"
        assert pc.duration_min_seconds is None
        assert pc.duration_max_seconds is None
        assert pc.playlist_id is None
        assert len(pc.id) == 36  # UUID format

    def test_roundtrip(self) -> None:
        pc = PipelineConfig(
            id="test-uuid",
            name="My Pipeline",
            enabled=False,
            playlist_id="PLabc",
            order=5,
            subscription_scope="selected",
            duration_min_seconds=60,
            duration_max_seconds=3600,
            selector_mode="OR",
        )
        data = pc.model_dump()
        pc2 = PipelineConfig.model_validate(data)
        assert pc == pc2


# ── PipelineCreate ──


class TestPipelineCreate:
    def test_minimal(self) -> None:
        pc = PipelineCreate(name="Test")
        assert pc.subscription_scope == "all"
        assert pc.selector_mode == "AND"
        assert pc.ignore_list_ids == []
        assert pc.selector_ids == []
        assert pc.subscription_ids == []

    def test_roundtrip(self) -> None:
        pc = PipelineCreate(
            name="Gaming",
            playlist_id="PL123",
            subscription_scope="selected",
            duration_min_seconds=300,
            duration_max_seconds=7200,
            selector_mode="OR",
            ignore_list_ids=["il-1", "il-2"],
            selector_ids=["sel-1"],
            subscription_ids=["sub-1", "sub-2"],
        )
        data = pc.model_dump()
        pc2 = PipelineCreate.model_validate(data)
        assert pc == pc2


# ── PipelineUpdate ──


class TestPipelineUpdate:
    def test_all_optional(self) -> None:
        pu = PipelineUpdate()
        data = pu.model_dump()
        assert all(v is None for v in data.values())

    def test_partial_update(self) -> None:
        pu = PipelineUpdate(name="New Name", enabled=False)
        assert pu.name == "New Name"
        assert pu.enabled is False
        assert pu.playlist_id is None


# ── PipelineResponse ──


class TestPipelineResponse:
    def test_roundtrip(self) -> None:
        pr = PipelineResponse(
            id="pipe-1",
            name="Tech",
            enabled=True,
            order=0,
            playlist_id="PLtech",
            subscription_scope="all",
            duration_min_seconds=300,
            duration_max_seconds=3600,
            selector_mode="AND",
            ignore_list_ids=["il-1"],
            selector_ids=["sel-1"],
            subscription_ids=["sub-1"],
        )
        data = pr.model_dump()
        pr2 = PipelineResponse.model_validate(data)
        assert pr == pr2


# ── RunSummary ──


class TestRunSummary:
    def test_defaults(self) -> None:
        rs = RunSummary()
        assert rs.status == "running"
        assert rs.trigger == "manual"
        assert rs.subscriptions_fetched == 0
        assert rs.videos_inserted == 0
        assert rs.quota_used == 0
        assert rs.id is None
        assert rs.error_message is None

    def test_roundtrip(self) -> None:
        rs = RunSummary(
            id="run-42",
            status="completed",
            trigger="scheduled",
            started_at="2026-07-12T12:00:00Z",
            completed_at="2026-07-12T12:02:15Z",
            subscriptions_fetched=195,
            activities_collected=847,
            videos_enriched=85,
            videos_inserted=12,
            videos_skipped=73,
            quota_used=756,
        )
        data = rs.model_dump()
        rs2 = RunSummary.model_validate(data)
        assert rs == rs2


# ── RunSummaryResponse ──


class TestRunSummaryResponse:
    def test_roundtrip(self) -> None:
        rsr = RunSummaryResponse(
            id="42",
            status="completed",
            trigger="manual",
            started_at="2026-07-12T12:00:00Z",
            completed_at="2026-07-12T12:02:15Z",
            subscriptions_fetched=195,
            activities_collected=847,
            videos_enriched=85,
            videos_inserted=12,
            videos_skipped=73,
            quota_used=756,
            error_message=None,
        )
        data = rsr.model_dump()
        rsr2 = RunSummaryResponse.model_validate(data)
        assert rsr == rsr2


# ── RunDecisionResponse ──


class TestRunDecisionResponse:
    def test_inserted(self) -> None:
        rd = RunDecisionResponse(
            run_id="42",
            pipeline_id="pipe-1",
            video_id="vid-1",
            action="inserted",
            filter_stage=None,
            filter_name=None,
            reason=None,
        )
        assert rd.action == "inserted"

    def test_skipped(self) -> None:
        rd = RunDecisionResponse(
            run_id="42",
            pipeline_id="pipe-1",
            video_id="vid-2",
            action="skipped",
            filter_stage="cheap",
            filter_name="word_filter",
            reason="Title contains blocked word",
        )
        assert rd.filter_stage == "cheap"
        assert rd.filter_name == "word_filter"


# ── PreviewRequest ──


class TestPreviewRequest:
    def test_null_pipeline(self) -> None:
        pr = PreviewRequest()
        assert pr.pipeline_id is None

    def test_specific_pipeline(self) -> None:
        pr = PreviewRequest(pipeline_id="pipe-1")
        assert pr.pipeline_id == "pipe-1"


# ── MockActivity ──


class TestMockActivity:
    def test_minimal(self) -> None:
        ma = MockActivity(
            video_id="mock-1",
            title="Test Video",
            channel_id="UC123",
            channel_title="Channel",
            subscription_id="sub-1",
            published_at="2026-07-12T00:00:00Z",
        )
        assert ma.activity_type == "upload"
        assert ma.description == ""
        assert ma.label == ""
        assert ma.duration_seconds is None

    def test_roundtrip(self) -> None:
        ma = MockActivity(
            video_id="mock-2",
            title="Long Video",
            description="A test video",
            channel_id="UC456",
            channel_title="Tech Channel",
            subscription_id="sub-2",
            published_at="2026-07-12T12:00:00Z",
            activity_type="playlistItem",
            duration_seconds=600,
            label="Duration filter: below min",
        )
        data = ma.model_dump()
        ma2 = MockActivity.model_validate(data)
        assert ma == ma2


# ── MockPreviewResponse ──


class TestMockPreviewResponse:
    def test_roundtrip(self) -> None:
        mpr = MockPreviewResponse(
            pipeline_id="pipe-1",
            pipeline_name="Tech",
            activities=[],
            results=[],
            quota_cost=0,
        )
        data = mpr.model_dump()
        mpr2 = MockPreviewResponse.model_validate(data)
        assert mpr == mpr2


# ── CachePreviewResponse ──


class TestCachePreviewResponse:
    def test_roundtrip(self) -> None:
        cpr = CachePreviewResponse(
            pipeline_id="pipe-1",
            pipeline_name="Tech",
            total_activities=847,
            activities_after_cheap=45,
            activities_after_duration=12,
            duration_unknown_count=3,
            quota_cost=0,
        )
        data = cpr.model_dump()
        cpr2 = CachePreviewResponse.model_validate(data)
        assert cpr == cpr2


# ── Activity ──


class TestActivity:
    def test_minimal(self) -> None:
        a = Activity(
            video_id="v1",
            title="My Video",
            published_at="2026-01-01T00:00:00Z",
            channel_id="UC123",
            channel_title="Channel",
        )
        assert a.description == ""
        assert a.subscription_id is None
        assert a.activity_type is None
        assert a.duration_seconds is None
        assert a.thumbnail_url is None

    def test_roundtrip(self) -> None:
        a = Activity(
            video_id="v2",
            title="Another Video",
            description="About stuff",
            published_at="2026-07-12T00:00:00Z",
            channel_id="UC456",
            channel_title="Tech",
            subscription_id="sub-1",
            activity_type="upload",
            duration_seconds=120,
            thumbnail_url="https://img.youtube.com/vi/v2/hqdefault.jpg",
        )
        data = a.model_dump()
        a2 = Activity.model_validate(data)
        assert a == a2


# ── Subscription ──


class TestSubscription:
    def test_minimal(self) -> None:
        s = Subscription(
            subscription_id="sub-1",
            channel_id="UC123",
            channel_title="Test Channel",
        )
        assert s.thumbnail_url is None

    def test_roundtrip(self) -> None:
        s = Subscription(
            subscription_id="sub-1",
            channel_id="UC123",
            channel_title="Test Channel",
            thumbnail_url="https://img.youtube.com/channel/UC123/hqdefault.jpg",
        )
        data = s.model_dump()
        s2 = Subscription.model_validate(data)
        assert s == s2


# ── Video ──


class TestVideo:
    def test_roundtrip(self) -> None:
        v = Video(
            video_id="v1",
            title="Video Title",
            channel_id="UC123",
            channel_title="Channel",
            published_at="2026-07-12T00:00:00Z",
            duration_seconds=300,
            pipeline_id="pipe-1",
            playlist_id="PLabc",
            inserted_at="2026-07-12T12:00:00Z",
        )
        data = v.model_dump()
        v2 = Video.model_validate(data)
        assert v == v2


# ── HealthResponse ──


class TestHealthResponse:
    def test_defaults(self) -> None:
        hr = HealthResponse()
        assert hr.status == "ok"
        assert hr.authenticated is False
        assert hr.quota_remaining == 10000

    def test_roundtrip(self) -> None:
        hr = HealthResponse(
            authenticated=True,
            pipelines_count=4,
            subscriptions_count=200,
            quota_used_today=756,
            quota_remaining=9244,
        )
        data = hr.model_dump()
        hr2 = HealthResponse.model_validate(data)
        assert hr == hr2


# ── ConfigResponse ──


class TestConfigResponse:
    def test_roundtrip(self) -> None:
        cr = ConfigResponse(
            schedule="0 */6 * * *",
            reprocess_days=2,
            activity_limit=0,
            subscription_limit=0,
            published_after=None,
            public_url="http://localhost:8080",
            log_level="warning",
        )
        data = cr.model_dump()
        cr2 = ConfigResponse.model_validate(data)
        assert cr == cr2


# ── ConfigUpdate ──


class TestConfigUpdate:
    def test_all_optional(self) -> None:
        cu = ConfigUpdate()
        data = cu.model_dump()
        assert all(v is None for v in data.values())

    def test_partial(self) -> None:
        cu = ConfigUpdate(schedule="0 0 * * *", log_level="debug")
        assert cu.schedule == "0 0 * * *"
        assert cu.log_level == "debug"
        assert cu.reprocess_days is None

    def test_roundtrip(self) -> None:
        cu = ConfigUpdate(
            schedule="0 0 * * *",
            reprocess_days=7,
            activity_limit=100,
            subscription_limit=50,
            published_after="2026-07-01T00:00:00Z",
            public_url="https://example.com",
            log_level="info",
        )
        data = cu.model_dump()
        cu2 = ConfigUpdate.model_validate(data)
        assert cu == cu2


# ── Settings (config.py) ──


class TestSettings:
    def test_defaults(self) -> None:
        s = Settings()
        assert s.schedule == "0 */6 * * *"
        assert s.reprocess_days == 2
        assert s.activity_limit == 0
        assert s.subscription_limit == 0
        assert s.published_after is None
        assert s.public_url == "http://localhost:8080"
        assert s.client_secret_path == "client_secret.json"
        assert s.database_file == "sortarr.db"
        assert s.log_level == "warning"
        assert s.api_port == 8080

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SORTARR_SCHEDULE", "0 0 * * *")
        monkeypatch.setenv("SORTARR_LOG_LEVEL", "debug")
        monkeypatch.setenv("SORTARR_ACTIVITY_LIMIT", "100")
        s = Settings()
        assert s.schedule == "0 0 * * *"
        assert s.log_level == "debug"
        assert s.activity_limit == 100

    def test_roundtrip(self) -> None:
        s = Settings()
        data = s.model_dump()
        s2 = Settings.model_validate(data)
        assert s == s2

    def test_model_dump_json(self) -> None:
        s = Settings()
        json_str = s.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["schedule"] == "0 */6 * * *"

    def test_load_settings_function(self) -> None:
        s = load_settings()
        assert isinstance(s, Settings)
        assert s.database_file == "sortarr.db"
