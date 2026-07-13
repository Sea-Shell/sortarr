#!/usr/bin/env python3
"""Migrate pipelines from v1 (my.db) to v2 (sortarr.db).

This script copies pipelines and their subscription associations from the v1
database to the v2 database. It is idempotent - running it multiple times is safe.

Schema differences:
- v1 has check_db_exists, check_title_similarity, compare_distance (removed in v2)
- Both share: id, name, enabled, selector_mode, duration_min/max_seconds,
  subscription_scope, destination_playlist_id, destination_playlist_title,
  sort_order, created_at, updated_at
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone


def migrate_pipelines(v1_db: str, v2_db: str, dry_run: bool = False):
    """Copy pipelines from v1 to v2 database.
    
    Args:
        v1_db: Path to v1 database (my.db)
        v2_db: Path to v2 database (sortarr.db)
        dry_run: If True, only print what would be done without making changes
    """
    # Verify source database exists
    if not Path(v1_db).exists():
        print(f"ERROR: Source database not found: {v1_db}")
        sys.exit(1)
    
    # Verify target database exists
    if not Path(v2_db).exists():
        print(f"ERROR: Target database not found: {v2_db}")
        sys.exit(1)
    
    v1_conn = sqlite3.connect(v1_db)
    v2_conn = sqlite3.connect(v2_db)
    
    v1_conn.row_factory = sqlite3.Row
    v2_conn.row_factory = sqlite3.Row
    
    try:
        # Get all pipelines from v1
        v1_pipelines = v1_conn.execute("SELECT * FROM pipelines ORDER BY sort_order, name").fetchall()
        
        print(f"Found {len(v1_pipelines)} pipelines in v1 database")
        print()
        
        # Get existing pipeline IDs in v2 to check for duplicates
        existing_ids = {row[0] for row in v2_conn.execute("SELECT id FROM pipelines").fetchall()}
        
        migrated_count = 0
        skipped_count = 0
        
        for pipeline in v1_pipelines:
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['name']
            
            if pipeline_id in existing_ids:
                print(f"⏭️  SKIP: Pipeline '{pipeline_name}' (id={pipeline_id}) already exists in v2")
                skipped_count += 1
                continue
            
            # Map v1 fields to v2 fields (excluding removed fields)
            v2_fields = {
                'id': pipeline['id'],
                'name': pipeline['name'],
                'enabled': pipeline['enabled'],
                'destination_playlist_id': pipeline['destination_playlist_id'],
                'destination_playlist_title': pipeline['destination_playlist_title'],
                'selector_mode': pipeline['selector_mode'],
                'subscription_scope': pipeline['subscription_scope'],
                'duration_min_seconds': pipeline['duration_min_seconds'],
                'duration_max_seconds': pipeline['duration_max_seconds'],
                'sort_order': pipeline['sort_order'],
                'created_at': pipeline['created_at'],
                'updated_at': pipeline['updated_at'],
            }
            
            if dry_run:
                print(f"🔍 DRY RUN: Would migrate pipeline '{pipeline_name}' (id={pipeline_id})")
                print(f"   Enabled: {bool(v2_fields['enabled'])}")
                print(f"   Playlist: {v2_fields['destination_playlist_title']}")
                print(f"   Duration: {v2_fields['duration_min_seconds']}-{v2_fields['duration_max_seconds']}s")
                print(f"   Selector: {v2_fields['selector_mode']}, Scope: {v2_fields['subscription_scope']}")
            else:
                # Insert pipeline into v2
                v2_conn.execute("""
                    INSERT INTO pipelines (
                        id, name, enabled, destination_playlist_id, destination_playlist_title,
                        selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
                        sort_order, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    v2_fields['id'],
                    v2_fields['name'],
                    v2_fields['enabled'],
                    v2_fields['destination_playlist_id'],
                    v2_fields['destination_playlist_title'],
                    v2_fields['selector_mode'],
                    v2_fields['subscription_scope'],
                    v2_fields['duration_min_seconds'],
                    v2_fields['duration_max_seconds'],
                    v2_fields['sort_order'],
                    v2_fields['created_at'],
                    v2_fields['updated_at'],
                ))
                
                print(f"✅ MIGRATED: Pipeline '{pipeline_name}' (id={pipeline_id})")
            
            # Get subscription associations for this pipeline
            subscriptions = v1_conn.execute(
                "SELECT subscription_id FROM pipeline_subscriptions WHERE pipeline_id = ?",
                (pipeline_id,)
            ).fetchall()
            
            if subscriptions:
                print(f"   📺 {len(subscriptions)} subscription(s) associated")
                
                if not dry_run:
                    # Copy subscription associations
                    for sub in subscriptions:
                        v2_conn.execute(
                            "INSERT INTO pipeline_subscriptions (pipeline_id, subscription_id) VALUES (?, ?)",
                            (pipeline_id, sub['subscription_id'])
                        )
            
            print()
            migrated_count += 1
        
        if not dry_run:
            v2_conn.commit()
            print(f"✅ Migration complete!")
        else:
            print(f"🔍 DRY RUN complete - no changes made")
        
        print(f"   Migrated: {migrated_count}")
        print(f"   Skipped (already exist): {skipped_count}")
        print(f"   Total in v1: {len(v1_pipelines)}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        if not dry_run:
            v2_conn.rollback()
        raise
    finally:
        v1_conn.close()
        v2_conn.close()


if __name__ == "__main__":
    v1_db = "/data/disk2/opt/sortarr/my.db"
    v2_db = "/data/disk2/opt/sortarr/sortarr.db"
    
    # Check for --dry-run flag
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    migrate_pipelines(v1_db, v2_db, dry_run=dry_run)

