"""Tests for sortarr.db.migrations — v2 schema creation and idempotency."""

import sqlite3

import pytest

from sortarr.db.migrations import (
    EXPECTED_INDEXES,
    EXPECTED_TABLE_COUNT,
    init_db,
)

EXPECTED_TABLES = [
    "subscriptions",
    "pipelines",
    "ignore_lists",
    "ignore_list_entries",
    "pipeline_ignore_lists",
    "pipeline_selectors",
    "pipeline_subscriptions",
    "subscription_tracking",
    "activity_cache",
    "videos",
    "pipeline_runs",
    "run_decisions",
    "app_config",
    "oauth_credentials",
]


@pytest.fixture
def conn():
    """In-memory connection with the v2 schema applied."""
    con = sqlite3.connect(":memory:")
    init_db(con)
    return con


def test_init_db_creates_all_tables(conn):
    """All 14 expected tables exist."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    for name in EXPECTED_TABLES:
        assert name in tables, f"missing table: {name}"
    assert len(tables) == EXPECTED_TABLE_COUNT


def test_init_db_creates_all_indexes(conn):
    """All expected indexes exist."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
    )
    indexes = {row[0] for row in cursor.fetchall()}
    for name in EXPECTED_INDEXES:
        assert name in indexes, f"missing index: {name}"
    assert len(indexes) == len(EXPECTED_INDEXES)


def test_init_db_idempotent():
    """Calling init_db twice on the same connection does not error."""
    con = sqlite3.connect(":memory:")
    init_db(con)
    init_db(con)  # second call must not raise
    # tables should still be exactly EXPECTED_TABLE_COUNT
    cursor = con.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    )
    assert cursor.fetchone()[0] == EXPECTED_TABLE_COUNT
