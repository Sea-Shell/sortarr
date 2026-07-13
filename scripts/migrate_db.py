#!/usr/bin/env python3
"""
Standalone database migration tool for sortarr.

Migrates v1 database (5 tables) to v2 schema (14 tables).
Creates backup before migration. Safe to run multiple times.

Usage:
    python scripts/migrate_db.py /path/to/sortarr.db
    python scripts/migrate_db.py /path/to/sortarr.db --no-backup
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path so we can import sortarr modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sortarr.db.migrate_v1_to_v2 import run_migration, detect_schema_version
import sqlite3


def setup_logging(verbose: bool = False):
    """Configure logging for migration script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Migrate sortarr database from v1 to v2 schema"
    )
    parser.add_argument(
        "database",
        type=Path,
        help="Path to sortarr.db file",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation (not recommended)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check schema version, don't migrate",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    log = logging.getLogger("migrate_db")
    
    # Validate database path
    if not args.database.exists():
        log.error(f"Database file not found: {args.database}")
        return 1
    
    # Check schema version
    log.info(f"Checking schema version: {args.database}")
    conn = sqlite3.connect(args.database)
    version = detect_schema_version(conn)
    conn.close()
    
    version_names = {
        0: "empty/new",
        1: "v1 (legacy 5-table schema)",
        2: "v2 (current 14-table schema)",
        -1: "unknown/corrupted",
    }
    
    log.info(f"Schema version: {version_names.get(version, 'unknown')}")
    
    if args.check_only:
        if version == 1:
            log.info("Migration needed: v1 → v2")
            return 0
        elif version == 2:
            log.info("No migration needed (already v2)")
            return 0
        else:
            log.error(f"Cannot migrate from version {version}")
            return 1
    
    # Run migration
    if version != 1:
        if version == 2:
            log.info("Database is already v2 - no migration needed")
            return 0
        else:
            log.error(f"Cannot migrate from version {version}")
            return 1
    
    log.info("Starting migration: v1 → v2")
    log.info("=" * 60)
    
    try:
        result = run_migration(
            args.database,
            create_backup_file=not args.no_backup,
        )
        
        if result["backup_path"]:
            log.info(f"Backup created: {result['backup_path']}")
        
        stats = result["stats"]
        log.info("=" * 60)
        log.info("Migration completed successfully!")
        log.info("")
        log.info("Summary:")
        log.info(f"  Subscriptions migrated: {stats['subscriptions_migrated']}")
        log.info(f"  Videos migrated: {stats['videos_migrated']}")
        log.info(f"  Last run migrated: {stats['last_run_migrated']}")
        log.info(f"  Default pipeline created: {stats['default_pipeline_created']}")
        log.info("")
        log.info("Next steps:")
        log.info("  1. Verify the migration by checking the database")
        log.info("  2. Configure pipelines in the web UI")
        log.info("  3. Enable the 'Migrated from v1' pipeline if needed")
        
        if result["backup_path"]:
            log.info("")
            log.info(f"Backup available at: {result['backup_path']}")
            log.info("To restore: cp backup-file sortarr.db")
        
        return 0
        
    except Exception as e:
        log.error(f"Migration failed: {e}")
        log.error("")
        log.error("Database has been rolled back to original state")
        if not args.no_backup:
            log.error("Backup file was created before migration attempt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
