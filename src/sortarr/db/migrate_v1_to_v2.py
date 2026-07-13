"""
sortarr.db.migrate_v1_to_v2 — Migration from v1 (archive) schema to v2.

Handles migration from the legacy 5-table schema (videos, last_run, channel,
subscription, playlist) to the modern 14-table v2 schema with pipelines,
selectors, ignore lists, and comprehensive audit trails.

Safe to run multiple times (idempotent). Creates timestamped backup before
starting. Can be run standalone or automatically on app startup.
"""

import sqlite3
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid

log = logging.getLogger("sortarr.db.migrate_v1_to_v2")


def detect_schema_version(conn: sqlite3.Connection) -> int:
    """Detect which schema version the database is using.
    
    Returns:
        0 = empty/new database
        1 = v1 schema (5 tables: videos, last_run, channel, subscription, playlist)
        2 = v2 schema (14 tables with pipelines, selectors, etc.)
        -1 = unknown/corrupted schema
    """
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    
    # Exclude sqlite internal tables
    tables.discard("sqlite_sequence")
    tables.discard("sqlite_master")
    
    if not tables:
        log.info("empty database detected (no tables)")
        return 0
    
    # V1 signature: has 'last_run' table (unique to v1)
    v1_signature = {"videos", "last_run", "channel", "subscription", "playlist"}
    if v1_signature.issubset(tables):
        log.info("v1 schema detected (5 tables)")
        return 1
    
    # V2 signature: has 'pipelines' and 'pipeline_selectors' (unique to v2)
    v2_signature = {"pipelines", "pipeline_selectors", "activity_cache", "run_decisions"}
    if v2_signature.issubset(tables):
        log.info("v2 schema detected (14 tables)")
        return 2
    
    # Mixed or unknown state
    log.warning(f"unknown schema detected - tables: {sorted(tables)}")
    return -1


def needs_migration(conn: sqlite3.Connection) -> bool:
    """Check if database needs migration from v1 to v2."""
    version = detect_schema_version(conn)
    return version == 1


def create_backup(db_path: Path) -> Path:
    """Create timestamped backup of database file.
    
    Returns path to backup file.
    Raises IOError if backup fails.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.name}.backup-{timestamp}"
    
    log.info(f"creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    # Verify backup
    if not backup_path.exists():
        raise IOError(f"backup file not created: {backup_path}")
    
    backup_size = backup_path.stat().st_size
    original_size = db_path.stat().st_size
    if backup_size != original_size:
        raise IOError(
            f"backup size mismatch: {backup_size} != {original_size}"
        )
    
    log.info(f"backup created successfully: {backup_path} ({backup_size} bytes)")
    return backup_path


def migrate_v1_to_v2(conn: sqlite3.Connection) -> dict:
    """Migrate v1 database to v2 schema.
    
    Preserves:
    - subscriptions (v1.subscription → v2.subscriptions)
    - videos audit trail (v1.videos → v2.videos)
    - last_run timestamp (v1.last_run → v2.app_config)
    
    Creates:
    - Default pipeline for migrated data
    - Subscription tracking entries
    
    Returns dict with migration statistics.
    """
    stats = {
        "subscriptions_migrated": 0,
        "videos_migrated": 0,
        "last_run_migrated": False,
        "default_pipeline_created": False,
    }
    
    log.info("starting v1 → v2 migration")
    
    # Import v2 schema
    from sortarr.db.migrations import V3_SCHEMA_SQL
    
    # Step 0: Rename v1 tables FIRST to avoid conflicts
    log.info("renaming v1 tables to _v1_archive suffix")
    v1_tables = ["videos", "last_run", "channel", "subscription", "playlist"]
    for table in v1_tables:
        try:
            conn.execute(f"ALTER TABLE {table} RENAME TO {table}_v1_archive")
        except sqlite3.OperationalError as e:
            # Table might not exist or already renamed
            log.debug(f"could not rename {table}: {e}")
    
    # Step 1: Create v2 tables (now safe after v1 tables renamed)
    log.info("creating v2 schema tables")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(V3_SCHEMA_SQL)
    
    # Step 2: Migrate subscriptions
    log.info("migrating subscriptions")
    cursor = conn.execute("""
        SELECT id, title, timestamp FROM subscription_v1_archive
    """)
    v1_subscriptions = cursor.fetchall()
    
    now_iso = datetime.now(timezone.utc).isoformat()
    for sub_id, title, timestamp in v1_subscriptions:
        # v1.subscription.timestamp was last fetch time
        last_seen = timestamp if timestamp else None
        created_at = timestamp if timestamp else now_iso
        
        conn.execute("""
            INSERT OR IGNORE INTO subscriptions 
            (id, title, channel_id, last_seen_at, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (sub_id, title, sub_id, last_seen, created_at))
        
        # Create tracking entry
        conn.execute("""
            INSERT OR IGNORE INTO subscription_tracking
            (subscription_id, last_fetched_at, updated_at)
            VALUES (?, ?, ?)
        """, (sub_id, last_seen, now_iso))
        
        stats["subscriptions_migrated"] += 1
    
    log.info(f"migrated {stats['subscriptions_migrated']} subscriptions")
    
    # Step 3: Create default pipeline for migrated videos
    log.info("creating default migration pipeline")
    pipeline_id = str(uuid.uuid4())
    
    # Get playlist info from v1 (if exists)
    cursor = conn.execute("SELECT id, title FROM playlist_v1_archive LIMIT 1")
    playlist_row = cursor.fetchone()
    if playlist_row:
        playlist_id, playlist_title = playlist_row
    else:
        playlist_id = "MIGRATED"
        playlist_title = "Migrated from v1"
    
    conn.execute("""
        INSERT INTO pipelines
        (id, name, enabled, destination_playlist_id, destination_playlist_title,
         selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
         sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pipeline_id,
        "Migrated from v1",
        0,  # disabled by default
        playlist_id,
        playlist_title,
        "AND",
        "all",
        0,
        0,
        999,  # low priority
        now_iso,
        now_iso,
    ))
    stats["default_pipeline_created"] = True
    
    # Step 4: Migrate videos
    log.info("migrating videos")
    cursor = conn.execute("""
        SELECT videoId, timestamp, title, subscriptionId FROM videos_v1_archive
    """)
    v1_videos = cursor.fetchall()
    
    for video_id, timestamp, title, subscription_id in v1_videos:
        inserted_at = timestamp if timestamp else now_iso
        
        conn.execute("""
            INSERT OR IGNORE INTO videos
            (video_id, title, duration_seconds, inserted_at, 
             pipeline_id, pipeline_name, playlist_id, playlist_title)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id,
            title,
            None,  # v1 didn't track duration
            inserted_at,
            pipeline_id,
            "Migrated from v1",
            playlist_id,
            playlist_title,
        ))
        
        stats["videos_migrated"] += 1
    
    log.info(f"migrated {stats['videos_migrated']} videos")
    
    # Step 5: Migrate last_run timestamp
    log.info("migrating last_run timestamp")
    cursor = conn.execute("SELECT timestamp FROM last_run_v1_archive WHERE id = 1 LIMIT 1")
    last_run_row = cursor.fetchone()
    if last_run_row:
        last_run_timestamp = last_run_row[0]
        conn.execute("""
            INSERT OR REPLACE INTO app_config (key, value)
            VALUES ('last_run_v1_migrated', ?)
        """, (last_run_timestamp,))
        stats["last_run_migrated"] = True
        log.info(f"migrated last_run: {last_run_timestamp}")
    
    # Step 6: Mark migration complete
    conn.execute("""
        INSERT OR REPLACE INTO app_config (key, value)
        VALUES ('schema_version', '2')
    """)
    conn.execute("""
        INSERT OR REPLACE INTO app_config (key, value)
        VALUES ('migrated_from_v1_at', ?)
    """, (now_iso,))
    
    conn.commit()
    log.info("v1 → v2 migration complete")
    
    return stats


def run_migration(db_path: Path, create_backup_file: bool = True) -> dict:
    """Run full migration workflow: detect, backup, migrate, verify.
    
    Args:
        db_path: Path to sortarr.db
        create_backup_file: Whether to create backup (default True)
    
    Returns:
        dict with migration results and statistics
    
    Raises:
        ValueError: if database is not v1 or migration not needed
        IOError: if backup fails
        sqlite3.Error: if migration fails
    """
    result = {
        "needed": False,
        "backup_path": None,
        "stats": {},
        "error": None,
    }
    
    if not db_path.exists():
        raise ValueError(f"database file not found: {db_path}")
    
    # Step 1: Detect version
    conn = sqlite3.connect(db_path)
    try:
        version = detect_schema_version(conn)
        
        if version == 0:
            raise ValueError("empty database - nothing to migrate")
        elif version == 2:
            log.info("database is already v2 - no migration needed")
            return result
        elif version == -1:
            raise ValueError("unknown schema - cannot migrate safely")
        elif version != 1:
            raise ValueError(f"unexpected schema version: {version}")
        
        result["needed"] = True
        
        # Step 2: Create backup
        if create_backup_file:
            result["backup_path"] = str(create_backup(db_path))
        
        # Step 3: Run migration
        stats = migrate_v1_to_v2(conn)
        result["stats"] = stats
        
        # Step 4: Verify v2 schema
        final_version = detect_schema_version(conn)
        if final_version != 2:
            raise RuntimeError(
                f"migration completed but schema is not v2 (got {final_version})"
            )
        
        log.info("migration verification passed")
        
    except Exception as e:
        result["error"] = str(e)
        log.error(f"migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    return result


def get_schema_version(conn: sqlite3.Connection) -> Optional[str]:
    """Get schema version from app_config table.
    
    Returns version string or None if not set.
    """
    try:
        cursor = conn.execute(
            "SELECT value FROM app_config WHERE key = 'schema_version' LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        # app_config table doesn't exist
        return None


