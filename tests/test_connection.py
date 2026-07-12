"""Tests for sortarr.db.connection — WAL mode, foreign keys, lifecycle."""

import sqlite3

import pytest

from sortarr.db.connection import (
    close_db,
    connection_ctx,
    get_connection,
    init_db,
)


@pytest.fixture(autouse=True)
def _reset_connection():
    """Ensure each test starts with no global connection."""
    close_db()
    yield
    close_db()


def test_init_db_returns_working_connection():
    """init_db(":memory:") returns a usable sqlite3.Connection."""
    conn = init_db(":memory:")
    assert isinstance(conn, sqlite3.Connection)
    result = conn.execute("SELECT 1").fetchone()
    assert result[0] == 1


def test_wal_mode_active_after_init(tmp_path):
    """PRAGMA journal_mode should be WAL after init_db (file-backed DB required)."""
    db_path = str(tmp_path / "wal_test.db")
    conn = init_db(db_path)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"


def test_foreign_keys_enabled_after_init():
    """PRAGMA foreign_keys should be ON after init_db."""
    conn = init_db(":memory:")
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1


def test_row_factory_is_row():
    """row_factory should be sqlite3.Row for dict-like access."""
    conn = init_db(":memory:")
    assert conn.row_factory is sqlite3.Row


def test_get_connection_returns_connection_after_init():
    """get_connection() should return the connection after init_db."""
    init_db(":memory:")
    conn = get_connection()
    assert isinstance(conn, sqlite3.Connection)


def test_get_connection_raises_before_init():
    """get_connection() should raise RuntimeError if init_db not called."""
    with pytest.raises(RuntimeError, match="database not initialized"):
        get_connection()


def test_close_db_works():
    """close_db() should close the connection and allow re-init."""
    init_db(":memory:")
    close_db()
    # After close, get_connection should raise
    with pytest.raises(RuntimeError):
        get_connection()
    # Re-init should work
    conn = init_db(":memory:")
    assert isinstance(conn, sqlite3.Connection)


def test_connection_ctx_commits_on_success():
    """connection_ctx should commit when no exception occurs."""
    conn = init_db(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
    with connection_ctx() as c:
        c.execute("INSERT INTO t (val) VALUES (?)", ("hello",))
    # Row should persist after commit
    row = conn.execute("SELECT val FROM t").fetchone()
    assert row["val"] == "hello"


def test_connection_ctx_rolls_back_on_exception():
    """connection_ctx should roll back when an exception occurs."""
    conn = init_db(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
    with pytest.raises(ValueError):
        with connection_ctx() as c:
            c.execute("INSERT INTO t (val) VALUES (?)", ("will_rollback",))
            raise ValueError("boom")
    # No rows should exist — rollback happened
    rows = conn.execute("SELECT * FROM t").fetchall()
    assert len(rows) == 0


def test_init_db_with_file_path(tmp_path):
    """init_db should work with a real file path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    conn.execute("CREATE TABLE t (id INTEGER)")
    conn.execute("INSERT INTO t (id) VALUES (1)")
    conn.commit()
    close_db()
    # Re-open same file — data persists
    conn = init_db(db_path)
    row = conn.execute("SELECT id FROM t").fetchone()
    assert row[0] == 1
