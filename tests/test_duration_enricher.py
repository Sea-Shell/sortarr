"""Tests for duration filter and batch enricher."""

import pytest

from sortarr.core.enricher import Enricher, parse_iso8601_duration
from sortarr.filters.duration_filter import check_duration
from sortarr.models.pipeline import FilterStage, PipelineConfig


def _make_pipeline(
    min_sec: int | None = None,
    max_sec: int | None = None,
) -> PipelineConfig:
    return PipelineConfig(
        name="test",
        duration_min_seconds=min_sec,
        duration_max_seconds=max_sec,
    )


class TestDurationFilterNoLimits:
    def test_returns_none_when_no_limits(self) -> None:
        pipeline = _make_pipeline()
        result = check_duration({"video_id": "abc"}, pipeline, {"duration_map": {"abc": 500}})
        assert result is None

    def test_returns_none_when_both_none(self) -> None:
        pipeline = _make_pipeline(min_sec=None, max_sec=None)
        result = check_duration({"video_id": "x"}, pipeline, {})
        assert result is None


class TestDurationFilterMinOnly:
    def test_rejects_below_min(self) -> None:
        pipeline = _make_pipeline(min_sec=600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 300}})
        assert result is not None
        assert result.passed is False
        assert result.filter_stage == FilterStage.DURATION
        assert result.reason is not None
        assert "minimum" in result.reason

    def test_accepts_at_min(self) -> None:
        pipeline = _make_pipeline(min_sec=600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 600}})
        assert result is None

    def test_accepts_above_min(self) -> None:
        pipeline = _make_pipeline(min_sec=600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 900}})
        assert result is None


class TestDurationFilterMaxOnly:
    def test_rejects_above_max(self) -> None:
        pipeline = _make_pipeline(max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 5000}})
        assert result is not None
        assert result.passed is False
        assert result.reason is not None
        assert "maximum" in result.reason

    def test_accepts_at_max(self) -> None:
        pipeline = _make_pipeline(max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 3600}})
        assert result is None

    def test_accepts_below_max(self) -> None:
        pipeline = _make_pipeline(max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 1200}})
        assert result is None


class TestDurationFilterBothBoundaries:
    def test_rejects_below_min(self) -> None:
        pipeline = _make_pipeline(min_sec=300, max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 100}})
        assert result is not None
        assert result.passed is False
        assert result.reason is not None
        assert "minimum" in result.reason

    def test_rejects_above_max(self) -> None:
        pipeline = _make_pipeline(min_sec=300, max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 5000}})
        assert result is not None
        assert result.passed is False
        assert result.reason is not None
        assert "maximum" in result.reason

    def test_accepts_within_range(self) -> None:
        pipeline = _make_pipeline(min_sec=300, max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 1800}})
        assert result is None


class TestDurationFilterUnknownDuration:
    """Unknown (None / 0) durations pass through with a warning — never blocked."""

    def test_none_duration_passes(self) -> None:
        pipeline = _make_pipeline(min_sec=60, max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {}})
        assert result is None

    def test_zero_duration_passes(self) -> None:
        pipeline = _make_pipeline(min_sec=60, max_sec=3600)
        result = check_duration({"video_id": "v1"}, pipeline, {"duration_map": {"v1": 0}})
        assert result is None

    def test_missing_from_map_passes(self) -> None:
        pipeline = _make_pipeline(min_sec=60)
        result = check_duration({"video_id": "not_in_map"}, pipeline, {"duration_map": {"other": 500}})
        assert result is None


class TestDurationFilterActivityKeys:
    """Activity dict may use 'video_id' or 'id' as the key."""

    def test_uses_video_id_key(self) -> None:
        pipeline = _make_pipeline(min_sec=600)
        result = check_duration({"video_id": "vid_A"}, pipeline, {"duration_map": {"vid_A": 300}})
        assert result is not None
        assert result.passed is False

    def test_falls_back_to_id_key(self) -> None:
        pipeline = _make_pipeline(min_sec=600)
        result = check_duration({"id": "vid_B"}, pipeline, {"duration_map": {"vid_B": 300}})
        assert result is not None
        assert result.passed is False


# ---------------------------------------------------------------------------
# ISO 8601 duration parser tests
# ---------------------------------------------------------------------------


class TestParseISO8601Duration:
    @pytest.mark.parametrize(
        ("input_str", "expected"),
        [
            ("PT1H30M15S", 5415),
            ("PT5M", 300),
            ("PT45S", 45),
            ("P1DT2H", 93600),
            ("PT0S", 0),
            ("PT1.5S", 2),
            ("PT1H", 3600),
            ("P2D", 172800),
            ("PT1H0M0S", 3600),
        ],
        ids=[
            "hms", "minutes-only", "seconds-only", "days-and-hours",
            "zero-seconds", "fractional-seconds-rounded", "hours-only",
            "days-only", "explicit-zeros",
        ],
    )
    def test_valid_durations(self, input_str: str, expected: int) -> None:
        assert parse_iso8601_duration(input_str) == expected

    @pytest.mark.parametrize(
        ("input_str", "expected"),
        [
            ("", None),
            ("not-a-duration", None),
            ("1H30M", None),
            ("PT", 0),
            ("random text", None),
        ],
        ids=["empty", "plain-text", "missing-t-prefix", "zero-duration", "random-text"],
    )
    def test_valid_and_invalid(self, input_str: str, expected: int | None) -> None:
        assert parse_iso8601_duration(input_str) is expected


# ---------------------------------------------------------------------------
# Enricher tests
# ---------------------------------------------------------------------------


def _video_item(video_id: str, duration: str) -> dict:
    return {"id": video_id, "contentDetails": {"duration": duration}}


class TestEnricherBatching:
    def test_100_ids_produces_2_api_calls(self) -> None:
        calls: list[str] = []

        def fake_api(ids_csv: str) -> dict:
            calls.append(ids_csv)
            return {"items": []}

        enricher = Enricher(fake_api)
        enricher.batch_fetch({f"vid{i:03d}" for i in range(100)})
        assert len(calls) == 2

    def test_exactly_50_ids_produces_1_call(self) -> None:
        calls: list[str] = []

        def fake_api(ids_csv: str) -> dict:
            calls.append(ids_csv)
            return {"items": []}

        enricher = Enricher(fake_api)
        enricher.batch_fetch({f"v{i}" for i in range(50)})
        assert len(calls) == 1

    def test_51_ids_produces_2_calls(self) -> None:
        calls: list[str] = []

        def fake_api(ids_csv: str) -> dict:
            calls.append(ids_csv)
            return {"items": []}

        enricher = Enricher(fake_api)
        enricher.batch_fetch({f"v{i}" for i in range(51)})
        assert len(calls) == 2

    def test_empty_set_makes_no_calls(self) -> None:
        calls: list[str] = []

        def fake_api(ids_csv: str) -> dict:
            calls.append(ids_csv)
            return {"items": []}

        enricher = Enricher(fake_api)
        result = enricher.batch_fetch(set())
        assert calls == []
        assert result == {}


class TestEnricherParsing:
    def test_parses_durations_from_response(self) -> None:
        def fake_api(ids_csv: str) -> dict:
            return {"items": [_video_item("a", "PT5M"), _video_item("b", "PT1H30M")]}

        enricher = Enricher(fake_api)
        result = enricher.batch_fetch({"a", "b"})
        assert result == {"a": 300, "b": 5400}

    def test_skips_items_without_duration(self) -> None:
        def fake_api(ids_csv: str) -> dict:
            return {"items": [_video_item("a", "PT5M"), {"id": "b"}]}

        enricher = Enricher(fake_api)
        result = enricher.batch_fetch({"a", "b"})
        assert result == {"a": 300}

    def test_skips_unparseable_duration(self) -> None:
        def fake_api(ids_csv: str) -> dict:
            return {"items": [_video_item("a", "PT5M"), _video_item("b", "INVALID")]}

        enricher = Enricher(fake_api)
        result = enricher.batch_fetch({"a", "b"})
        assert result == {"a": 300}


class TestEnricherErrorHandling:
    def test_api_error_continues_to_next_batch(self) -> None:
        call_count = 0

        def flaky_api(ids_csv: str) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("network timeout")
            return {"items": [_video_item("ok", "PT2M")]}

        enricher = Enricher(flaky_api)
        ids = {"ok", *[f"bad{i}" for i in range(50)]}
        result = enricher.batch_fetch(ids)
        assert "ok" in result
        assert result["ok"] == 120

    def test_total_api_failure_returns_empty(self) -> None:
        def boom(ids_csv: str) -> dict:
            raise RuntimeError("down")

        enricher = Enricher(boom)
        result = enricher.batch_fetch({"a", "b"})
        assert result == {}

    def test_exception_does_not_crash_enricher(self) -> None:
        def always_fail(ids_csv: str) -> dict:
            raise ValueError("bad request")

        enricher = Enricher(always_fail)
        result = enricher.batch_fetch({f"v{i}" for i in range(200)})
        assert isinstance(result, dict)
        assert result == {}
