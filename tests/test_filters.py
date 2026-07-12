"""Tests for sortarr.filters — cheap filter modules + chain engine.

Each filter module has at least 3 cases: pass, fail, edge case.
The chain tests verify ordering and short-circuit behavior.
"""

from __future__ import annotations

import pytest

from sortarr.core.filters import FILTER_REGISTRY, FilterChain
from sortarr.filters import (  # noqa: F401 — trigger registrations
    db_exists,
    ignore_list,
    selector_filter,
    title_similarity,
    word_filter,
)
from sortarr.filters.db_exists import check_db_exists
from sortarr.filters.ignore_list import check_subscription_ignore, check_video_ignore
from sortarr.filters.selector_filter import _apply_operator, check_selectors
from sortarr.filters.title_similarity import (
    _fuzz_ratio,
    _levenshtein,
    _normalize,
    check_title_similarity,
)
from sortarr.filters.word_filter import check_word_filter
from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig


@pytest.fixture
def pipeline() -> PipelineConfig:
    return PipelineConfig(name="test-pipeline")


def _act(**overrides) -> dict:
    """Build an activity dict with sensible defaults."""
    base = {
        "video_id": "vid_001",
        "title": "A Great Video",
        "description": "About something interesting",
        "channel_id": "UC_test",
        "channel_title": "Test Channel",
        "subscription_id": "sub_001",
        "published_at": "2026-07-01T00:00:00Z",
        "activity_type": "upload",
    }
    base.update(overrides)
    return base


# ===========================================================================
# Word Filter
# ===========================================================================


class TestWordFilter:
    def test_match_found(self, pipeline):
        ctx = {"word_ignore_values": {"python", "tutorial"}}
        act = _act(title="Learn Python Programming")
        result = check_word_filter(act, pipeline, ctx)
        assert result is not None
        assert not result.passed
        assert result.filter_name == "word_filter"
        assert "python" in result.reason

    def test_no_match_passes(self, pipeline):
        ctx = {"word_ignore_values": {"python", "tutorial"}}
        act = _act(title="Cooking with Rust")
        result = check_word_filter(act, pipeline, ctx)
        assert result is None

    def test_case_insensitive(self, pipeline):
        ctx = {"word_ignore_values": {"python"}}
        act = _act(title="PYTHON Tutorial 101")
        result = check_word_filter(act, pipeline, ctx)
        assert result is not None
        assert not result.passed

    def test_empty_ignore_set(self, pipeline):
        ctx = {"word_ignore_values": set()}
        act = _act(title="Anything goes")
        assert check_word_filter(act, pipeline, ctx) is None

    def test_no_context_key(self, pipeline):
        act = _act(title="Whatever")
        assert check_word_filter(act, pipeline, {}) is None

    def test_empty_title(self, pipeline):
        ctx = {"word_ignore_values": {"python"}}
        act = _act(title="")
        assert check_word_filter(act, pipeline, ctx) is None

    def test_substring_match(self, pipeline):
        ctx = {"word_ignore_values": {"hack"}}
        act = _act(title="Lifehack for productivity")
        result = check_word_filter(act, pipeline, ctx)
        assert result is not None
        assert not result.passed


# ===========================================================================
# Ignore List — Subscription
# ===========================================================================


class TestSubscriptionIgnore:
    def test_sub_in_ignore_list(self, pipeline):
        ctx = {"subscription_ignore_ids": {"sub_001", "sub_002"}}
        act = _act(subscription_id="sub_001")
        result = check_subscription_ignore(act, pipeline, ctx)
        assert result is not None
        assert not result.passed
        assert result.filter_name == "subscription_ignore"

    def test_sub_not_in_ignore_list(self, pipeline):
        ctx = {"subscription_ignore_ids": {"sub_999"}}
        act = _act(subscription_id="sub_001")
        assert check_subscription_ignore(act, pipeline, ctx) is None

    def test_empty_ignore_set(self, pipeline):
        ctx = {"subscription_ignore_ids": set()}
        act = _act(subscription_id="sub_001")
        assert check_subscription_ignore(act, pipeline, ctx) is None

    def test_no_subscription_id(self, pipeline):
        ctx = {"subscription_ignore_ids": {"sub_001"}}
        act = _act()
        act.pop("subscription_id")
        assert check_subscription_ignore(act, pipeline, ctx) is None


# ===========================================================================
# Ignore List — Video
# ===========================================================================


class TestVideoIgnore:
    def test_video_in_ignore_list(self, pipeline):
        ctx = {"video_ignore_ids": {"vid_001", "vid_002"}}
        act = _act(video_id="vid_001")
        result = check_video_ignore(act, pipeline, ctx)
        assert result is not None
        assert not result.passed
        assert result.filter_name == "video_ignore"

    def test_video_not_in_ignore_list(self, pipeline):
        ctx = {"video_ignore_ids": {"vid_999"}}
        act = _act(video_id="vid_001")
        assert check_video_ignore(act, pipeline, ctx) is None

    def test_empty_ignore_set(self, pipeline):
        ctx = {"video_ignore_ids": set()}
        act = _act(video_id="vid_001")
        assert check_video_ignore(act, pipeline, ctx) is None

    def test_no_video_id(self, pipeline):
        ctx = {"video_ignore_ids": {"vid_001"}}
        act = _act()
        act.pop("video_id")
        assert check_video_ignore(act, pipeline, ctx) is None


# ===========================================================================
# Title Similarity
# ===========================================================================


class TestNormalize:
    def test_basic(self):
        assert _normalize("Hello World!") == "hello world"

    def test_collapses_special_chars(self):
        assert _normalize("Hello---World!!!") == "hello world"

    def test_empty(self):
        assert _normalize("") == ""


class TestLevenshtein:
    def test_identical(self):
        assert _levenshtein("abc", "abc") == 0

    def test_empty_strings(self):
        assert _levenshtein("", "") == 0
        assert _levenshtein("abc", "") == 3
        assert _levenshtein("", "abc") == 3

    def test_single_edit(self):
        assert _levenshtein("kitten", "sitting") == 3


class TestFuzzRatio:
    def test_identical(self):
        assert _fuzz_ratio("hello", "hello") == 100

    def test_empty_strings(self):
        assert _fuzz_ratio("", "") == 0
        assert _fuzz_ratio("abc", "") == 0

    def test_completely_different(self):
        assert _fuzz_ratio("abc", "xyz") == 0

    def test_symmetric(self):
        assert _fuzz_ratio("abcdef", "abcxyz") == _fuzz_ratio("abcxyz", "abcdef")

    def test_kitten_sitting(self):
        ratio = _fuzz_ratio("kitten", "sitting")
        assert 55 <= ratio <= 60


class TestTitleSimilarityFilter:
    def test_duplicate_rejected(self, pipeline):
        ctx = {
            "recent_videos": [{"video_id": "v1", "title": "Hello World"}],
            "compare_distance": 80,
        }
        act = _act(title="Hello World")
        result = check_title_similarity(act, pipeline, ctx)
        assert result is not None
        assert not result.passed
        assert result.filter_name == "title_similarity"

    def test_different_titles_pass(self, pipeline):
        ctx = {
            "recent_videos": [{"video_id": "v1", "title": "Completely Different Topic"}],
            "compare_distance": 80,
        }
        act = _act(title="Unique New Title")
        assert check_title_similarity(act, pipeline, ctx) is None

    def test_empty_recent_videos(self, pipeline):
        ctx = {"recent_videos": [], "compare_distance": 80}
        act = _act(title="Anything")
        assert check_title_similarity(act, pipeline, ctx) is None

    def test_near_duplicate_rejected(self, pipeline):
        ctx = {
            "recent_videos": [{"video_id": "v1", "title": "Python Tutorial for Beginners"}],
            "compare_distance": 80,
        }
        act = _act(title="Python Tutorial For Beginners")
        result = check_title_similarity(act, pipeline, ctx)
        assert result is not None
        assert not result.passed

    def test_below_threshold_passes(self, pipeline):
        ctx = {
            "recent_videos": [{"video_id": "v1", "title": "Cooking Pasta"}],
            "compare_distance": 80,
        }
        act = _act(title="Advanced Rust Concurrency")
        assert check_title_similarity(act, pipeline, ctx) is None

    def test_empty_title(self, pipeline):
        ctx = {
            "recent_videos": [{"video_id": "v1", "title": "Something"}],
            "compare_distance": 80,
        }
        act = _act(title="")
        assert check_title_similarity(act, pipeline, ctx) is None

    def test_long_title_truncation_performance(self, pipeline):
        """Long titles are truncated to prevent O(n*m) explosion."""
        import time

        # 5000-char title
        long_title = "a" * 5000
        ctx = {
            "recent_videos": [{"video_id": "v1", "title": "b" * 5000}],  # Also 5000 chars, totally different
            "compare_distance": 80,
        }
        act = _act(title=long_title, video_id="new_video")

        start = time.time()
        result = check_title_similarity(act, pipeline, ctx)
        elapsed = time.time() - start

        # Should complete in under 100ms (not 3+ seconds)
        assert elapsed < 0.1, f"title_similarity took {elapsed:.2f}s — should be <0.1s with truncation"
        # Should pass (titles are different even after truncation)
        assert result is None  # None = passed


# ===========================================================================
# Selector Filter
# ===========================================================================


class TestApplyOperator:
    def test_contains_match(self):
        assert _apply_operator("Python Tutorial", "contains", "python") is True

    def test_contains_no_match(self):
        assert _apply_operator("Hello World", "contains", "python") is False

    def test_not_contains(self):
        assert _apply_operator("Hello World", "not_contains", "python") is True

    def test_equals_case_insensitive(self):
        assert _apply_operator("Python", "equals", "python") is True

    def test_not_equals(self):
        assert _apply_operator("Python", "not_equals", "golang") is True

    def test_starts_with(self):
        assert _apply_operator("Python Tutorial", "starts_with", "python") is True

    def test_ends_with(self):
        assert _apply_operator("Python Tutorial", "ends_with", "tutorial") is True

    def test_regex_match(self):
        assert _apply_operator("Python 2024", "regex", r"\d{4}") is True

    def test_regex_no_match(self):
        assert _apply_operator("Python Tutorial", "regex", r"^\d+$") is False

    def test_unknown_operator(self):
        assert _apply_operator("test", "unknown_op", "test") is False


class TestSelectorFilter:
    def test_no_selectors_passes(self, pipeline):
        act = _act()
        assert check_selectors(act, pipeline, {}) is None

    def test_and_mode_all_match(self, pipeline):
        ctx = {
            "selectors": [
                {"field": "title", "operator": "contains", "pattern": "python"},
                {"field": "title", "operator": "contains", "pattern": "tutorial"},
            ]
        }
        pipeline.selector_mode = "AND"
        act = _act(title="Python Tutorial 2024")
        assert check_selectors(act, pipeline, ctx) is None

    def test_and_mode_one_fails(self, pipeline):
        ctx = {
            "selectors": [
                {"field": "title", "operator": "contains", "pattern": "python"},
                {"field": "title", "operator": "contains", "pattern": "golang"},
            ]
        }
        pipeline.selector_mode = "AND"
        act = _act(title="Python Tutorial 2024")
        result = check_selectors(act, pipeline, ctx)
        assert result is not None
        assert not result.passed

    def test_or_mode_any_match(self, pipeline):
        ctx = {
            "selectors": [
                {"field": "title", "operator": "contains", "pattern": "golang"},
                {"field": "title", "operator": "contains", "pattern": "python"},
            ]
        }
        pipeline.selector_mode = "OR"
        act = _act(title="Python Tutorial 2024")
        assert check_selectors(act, pipeline, ctx) is None

    def test_or_mode_none_match(self, pipeline):
        ctx = {
            "selectors": [
                {"field": "title", "operator": "contains", "pattern": "golang"},
                {"field": "title", "operator": "contains", "pattern": "rust"},
            ]
        }
        pipeline.selector_mode = "OR"
        act = _act(title="Python Tutorial 2024")
        result = check_selectors(act, pipeline, ctx)
        assert result is not None
        assert not result.passed

    def test_channel_title_field(self, pipeline):
        ctx = {
            "selectors": [
                {"field": "channel_title", "operator": "contains", "pattern": "Test"}
            ]
        }
        act = _act(channel_title="Test Channel")
        assert check_selectors(act, pipeline, ctx) is None

    def test_regex_selector(self, pipeline):
        ctx = {
            "selectors": [
                {"field": "title", "operator": "regex", "pattern": r".*[Tt]utorial.*"}
            ]
        }
        act = _act(title="Python Tutorial 2024")
        assert check_selectors(act, pipeline, ctx) is None

    def test_description_field(self, pipeline):
        ctx = {
            "selectors": [
                {"field": "description", "operator": "contains", "pattern": "interesting"}
            ]
        }
        act = _act(description="About something interesting")
        assert check_selectors(act, pipeline, ctx) is None

    def test_regex_nested_quantifiers_rejected(self, pipeline):
        """Nested quantifiers are rejected to prevent ReDoS attacks."""
        ctx = {
            "selectors": [
                {
                    "field": "title",
                    "operator": "regex",
                    "pattern": r"(a+)+b",  # nested quantifiers — potential ReDoS
                }
            ]
        }
        pipeline.selector_mode = "AND"
        act = _act(title="a" * 30 + "X")  # No 'b' at end
        result = check_selectors(act, pipeline, ctx)
        # Should return FilterResult(passed=False) due to pattern rejection
        assert result is not None
        assert not result.passed
        assert "not matched" in result.reason.lower()


# ===========================================================================
# DB Exists
# ===========================================================================


class TestDbExists:
    def test_video_exists(self, pipeline):
        ctx = {"existing_video_ids": {"vid_001", "vid_002"}}
        act = _act(video_id="vid_001")
        result = check_db_exists(act, pipeline, ctx)
        assert result is not None
        assert not result.passed
        assert result.filter_name == "db_exists"

    def test_video_not_exists(self, pipeline):
        ctx = {"existing_video_ids": {"vid_999"}}
        act = _act(video_id="vid_001")
        assert check_db_exists(act, pipeline, ctx) is None

    def test_empty_existing_set(self, pipeline):
        ctx = {"existing_video_ids": set()}
        act = _act(video_id="vid_001")
        assert check_db_exists(act, pipeline, ctx) is None

    def test_no_video_id(self, pipeline):
        ctx = {"existing_video_ids": {"vid_001"}}
        act = _act()
        act.pop("video_id")
        assert check_db_exists(act, pipeline, ctx) is None


# ===========================================================================
# Filter Registration
# ===========================================================================


class TestFilterRegistration:
    def test_all_filters_registered(self):
        """Verify all expected cheap filters are in the registry."""
        names = [name for name, _, stage in FILTER_REGISTRY if stage == FilterStage.CHEAP]
        expected = [
            "subscription_ignore",
            "video_ignore",
            "word_filter",
            "db_exists",
            "title_similarity",
            "selector_filter",
        ]
        assert names == expected

    def test_registration_order_matches_architect_spec(self):
        """Order: subscription_scope (runner-inline) → sub_ignore → video_ignore →
        word_filter → db_exists → title_similarity → selectors.
        """
        names = [name for name, _, stage in FILTER_REGISTRY if stage == FilterStage.CHEAP]
        assert names.index("subscription_ignore") < names.index("video_ignore")
        assert names.index("video_ignore") < names.index("word_filter")
        assert names.index("word_filter") < names.index("db_exists")
        assert names.index("db_exists") < names.index("title_similarity")
        assert names.index("title_similarity") < names.index("selector_filter")


# ===========================================================================
# FilterChain — integration tests
# ===========================================================================


class TestFilterChain:
    def test_all_pass_returns_none(self, pipeline):
        """Activity that passes all filters returns None."""
        ctx = {
            "word_ignore_values": set(),
            "subscription_ignore_ids": set(),
            "video_ignore_ids": set(),
            "existing_video_ids": set(),
            "recent_videos": [],
            "compare_distance": 80,
            "selectors": [],
        }
        chain = FilterChain(pipeline, ctx)
        act = _act()
        assert chain.run_cheap_filters(act) is None

    def test_short_circuit_prevents_later_filters(self, pipeline):
        """If word_filter fails, db_exists is NOT called."""
        call_log: list[str] = []

        def mock_sub(activity, pipe, context):
            call_log.append("subscription_ignore")
            return None

        def mock_word(activity, pipe, context):
            call_log.append("word_filter")
            return FilterResult(
                filter_stage=FilterStage.CHEAP,
                filter_name="word_filter",
                passed=False,
                reason="hit",
            )

        def mock_db(activity, pipe, context):
            call_log.append("db_exists")
            return FilterResult(
                filter_stage=FilterStage.CHEAP,
                filter_name="db_exists",
                passed=False,
                reason="hit",
            )

        original = FILTER_REGISTRY.copy()
        try:
            FILTER_REGISTRY.clear()
            FILTER_REGISTRY.append(("subscription_ignore", mock_sub, FilterStage.CHEAP))
            FILTER_REGISTRY.append(("word_filter", mock_word, FilterStage.CHEAP))
            FILTER_REGISTRY.append(("db_exists", mock_db, FilterStage.CHEAP))

            chain = FilterChain(pipeline, {})
            result = chain.run_cheap_filters(_act())

            assert result is not None
            assert result.filter_name == "word_filter"
            assert "db_exists" not in call_log
        finally:
            FILTER_REGISTRY.clear()
            FILTER_REGISTRY.extend(original)

    def test_subscription_scope_not_in_registry(self, pipeline):
        """subscription_scope is handled by the runner, not registered."""
        names = [name for name, _, _ in FILTER_REGISTRY]
        assert "subscription_scope" not in names

    def test_empty_context_passes_through(self, pipeline):
        """With no context keys, all cheap filters should pass (no-ops)."""
        chain = FilterChain(pipeline, {})
        act = _act()
        assert chain.run_cheap_filters(act) is None
