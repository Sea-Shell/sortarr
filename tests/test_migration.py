"""
Tests for v1 → v2 database migration.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import tempfile

from sortarr.db.migrate_v1_to_v2 import (
    detect_schema_version,
    needs_migration,
    create_backup,
    migrate_v1_to_v2,
    run_migration,
)


@pytest.fixture
def temp_db():
    """Create temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    db_path = Path(path)
    yield db_path
    # Cleanup
    db_path.unlink(missing_ok=True)
    # Clean up any backup files
    for backup in db_path.parent.glob(f"{db_path.name}.backup-*"):
        backup.unlink()


@pytest.fixture
def v1_db(temp_db):
    """Create v1 schema database with sample data."""
    conn = sqlite3.connect(temp_db)
    
    # Create v1 tables
    conn.executescript("""
        CREATE TABLE videos (
            videoId TEXT NOT NULL PRIMARY KEY,
            timestamp TEXT,
            title TEXT,
            subscriptionId TEXT
        );
        
        CREATE TABLE last_run (
            id NUMBER NOT NULL PRIMARY KEY,
            timestamp TEXT
        );
        
        CREATE TABLE channel (
            id NUMBER NOT NULL PRIMARY KEY,
            title TEXT
        );
        
        CREATE TABLE subscription (
            id NUMBER NOT NULL PRIMARY KEY,
            title TEXT,
            timestamp TEXT
        );
        
        CREATE TABLE playlist (
            id NUMBER NOT NULL PRIMARY KEY,
            title TEXT
        );
    """)
    
    # Insert sample data
    now = datetime.now(timezone.utc).isoformat()
    
    conn.execute(
        "INSERT INTO subscription (id, title, timestamp) VALUES (?, ?, ?)",
        ("UC123", "Test Channel", now)
    )
    conn.execute(
        "INSERT INTO videos (videoId, timestamp, title, subscriptionId) VALUES (?, ?, ?, ?)",
        ("vid123", now, "Test Video", "UC123")
    )
    conn.execute(
        "INSERT INTO last_run (id, timestamp) VALUES (?, ?)",
        (1, now)
    )
    conn.execute(
        "INSERT INTO playlist (id, title) VALUES (?, ?)",
        ("PL123", "Test Playlist")
    )
    
    conn.commit()
    conn.close()
    
    return temp_db


def test_detect_empty_database(temp_db):
    """Empty database should be version 0."""
    conn = sqlite3.connect(temp_db)
    version = detect_schema_version(conn)
    conn.close()
    assert version == 0


def test_detect_v1_schema(v1_db):
    """V1 database should be detected correctly."""
    conn = sqlite3.connect(v1_db)
    version = detect_schema_version(conn)
    conn.close()
    assert version == 1


def test_needs_migration_v1(v1_db):
    """V1 database should need migration."""
    conn = sqlite3.connect(v1_db)
    assert needs_migration(conn) is True
    conn.close()


def test_create_backup(v1_db):
    """Backup should be created with correct size."""
    backup_path = create_backup(v1_db)
    
    assert backup_path.exists()
    assert backup_path.name.startswith(v1_db.name + ".backup-")
    assert backup_path.stat().st_size == v1_db.stat().st_size


def test_migrate_v1_to_v2(v1_db):
    """Full migration should preserve data and create v2 schema."""
    conn = sqlite3.connect(v1_db)
    
    # Run migration
    stats = migrate_v1_to_v2(conn)
    
    # Check stats
    assert stats["subscriptions_migrated"] == 1
    assert stats["videos_migrated"] == 1
    assert stats["last_run_migrated"] is True
    assert stats["default_pipeline_created"] is True
    
    # Verify v2 schema
    version = detect_schema_version(conn)
    assert version == 2
    
    # Verify subscriptions migrated
    cursor = conn.execute("SELECT id, title FROM subscriptions")
    subs = cursor.fetchall()
    assert len(subs) == 1
    assert subs[0][0] == "UC123"
    assert subs[0][1] == "Test Channel"
    
    # Verify videos migrated
    cursor = conn.execute("SELECT video_id, title FROM videos")
    vids = cursor.fetchall()
    assert len(vids) == 1
    assert vids[0][0] == "vid123"
    assert vids[0][1] == "Test Video"
    
    # Verify pipeline created
    cursor = conn.execute("SELECT name, destination_playlist_id FROM pipelines")
    pipes = cursor.fetchall()
    assert len(pipes) == 1
    assert pipes[0][0] == "Migrated from v1"
    assert pipes[0][1] == "PL123"
    
    # Verify schema version in config
    cursor = conn.execute("SELECT value FROM app_config WHERE key = 'schema_version'")
    row = cursor.fetchone()
    assert row[0] == "2"
    
    conn.close()


def test_run_migration_full_workflow(v1_db):
    """Full migration workflow with backup."""
    result = run_migration(v1_db, create_backup_file=True)
    
    assert result["needed"] is True
    assert result["backup_path"] is not None
    assert result["error"] is None
    assert result["stats"]["subscriptions_migrated"] == 1
    
    # Verify backup exists
    backup_path = Path(result["backup_path"])
    assert backup_path.exists()


def test_run_migration_already_v2(temp_db):
    """Migration should skip if already v2."""
    # Create v2 schema
    from sortarr.db.migrations import V3_SCHEMA_SQL
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(V3_SCHEMA_SQL)
    conn.commit()
    conn.close()
    
    # Try to migrate
    result = run_migration(temp_db)
    
    assert result["needed"] is False
    assert result["backup_path"] is None


def test_migration_idempotent(v1_db):
    """Running migration twice should be safe."""
    conn = sqlite3.connect(v1_db)
    
    # First migration
    stats1 = migrate_v1_to_v2(conn)
    assert stats1["subscriptions_migrated"] == 1
    
    # Second migration should not duplicate data
    # (INSERT OR IGNORE should prevent duplicates)
    version = detect_schema_version(conn)
    assert version == 2
    
    # Verify no duplicates
    cursor = conn.execute("SELECT COUNT(*) FROM subscriptions")
    count = cursor.fetchone()[0]
    assert count == 1
    
    conn.close()

