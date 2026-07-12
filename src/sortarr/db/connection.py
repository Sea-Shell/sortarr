"""sortarr.db.connection — SQLite connection management with WAL mode.

Provides a module-level connection lifecycle for the application.
All connections use sqlite3.Row row_factory, WAL journal mode,
and foreign key enforcement.
"""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

log = logging.getLogger("sortarr.db.connection")

_connection: sqlite3.Connection | None = None


def init_db(db_path: str = "sortarr.db") -> sqlite3.Connection:
    """Initialize the database connection with WAL mode and foreign keys.

    Called once at application startup (FastAPI lifespan).
    Creates the database file if it doesn't exist.
    """
    global _connection

    _connection = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
        check_same_thread=False,
    )
    _connection.row_factory = sqlite3.Row

    # Enable WAL mode for concurrent read access during writes
    _connection.execute("PRAGMA journal_mode=WAL")
    # Enable foreign key enforcement (off by default in sqlite3)
    _connection.execute("PRAGMA foreign_keys=ON")
    # Busy timeout: wait up to 5 seconds on lock contention
    _connection.execute("PRAGMA busy_timeout=5000")

    log.info("database initialized: %s (WAL mode, foreign keys on)", db_path)
    return _connection


def close_db() -> None:
    """Close the database connection. Called at application shutdown."""
    global _connection

    if _connection is not None:
        _connection.close()
        log.info("database connection closed")
        _connection = None


def get_connection() -> sqlite3.Connection:
    """Get the module-level database connection.

    Raises RuntimeError if init_db() has not been called.
    """
    if _connection is None:
        raise RuntimeError("database not initialized: call init_db() first")
    return _connection


@contextmanager
def connection_ctx() -> Generator[sqlite3.Connection, None, None]:
    """Context manager providing a transactional database connection.

    Commits on success, rolls back on exception.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
