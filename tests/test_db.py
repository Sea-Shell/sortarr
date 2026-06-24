import pytest
import sqlite3
from sortarr.db.migrations import init_db
from sortarr.db.repository.videos import (
    video_exists,
    insert_video,
    get_all_video_titles,
    insert_channel,
    get_channel,
    insert_playlist,
    get_playlist,
    insert_subscription,
    get_subscription_timestamp,
    get_last_run,
    set_last_run,
)
from sortarr.db.repository.pipeline import (
    get_routing_rules,
    create_routing_rule,
    update_routing_rule,
    delete_routing_rule,
    get_pipelines,
    create_pipeline,
    reorder_pipelines,
)
from sortarr.db.repository.pipeline_runs import (
    create_pipeline_run,
    finish_pipeline_run,
    get_pipeline_runs,
    get_pipeline_run,
)
from sortarr.db.repository.config import (
    get_config,
    set_config,
    get_ignore_entries,
    add_ignore_entry,
    update_ignore_entry,
    delete_ignore_entry,
)


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cursor = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    con.close()
    assert "videos" in tables
    assert "channel" in tables
    assert "playlist" in tables
    assert "subscription" in tables
    assert "last_run" in tables
    assert "routing_rules" in tables
    assert "pipeline_runs" in tables
    assert "app_config" in tables
    assert "ignore_entries" in tables


@pytest.fixture
def db_con(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    yield con
    con.close()


def test_video_crud(db_con):
    assert not video_exists(db_con, "v1")
    assert insert_video(db_con, "v1", "now", "Test", "sub1")
    assert video_exists(db_con, "v1")
    titles = get_all_video_titles(db_con)
    assert len(titles) == 1
    assert titles[0][1] == "Test"


def test_channel_crud(db_con):
    assert get_channel(db_con) is None
    assert insert_channel(db_con, "UC1", "My Channel")
    ch = get_channel(db_con)
    assert ch["id"] == "UC1"


def test_playlist_crud(db_con):
    assert get_playlist(db_con) is None
    assert insert_playlist(db_con, "PL1", "My Playlist")
    pl = get_playlist(db_con)
    assert pl["id"] == "PL1"


def test_subscription_crud(db_con):
    assert get_subscription_timestamp(db_con, "s1") is None
    assert insert_subscription(db_con, "s1", "Sub", "2024-01-01")
    assert get_subscription_timestamp(db_con, "s1") == "2024-01-01"


def test_last_run(db_con):
    assert get_last_run(db_con) is None
    assert set_last_run(db_con, "now")
    assert get_last_run(db_con) == "now"


def test_routing_rules(db_con):
    rules = get_routing_rules(db_con)
    assert len(rules) == 0
    rid = create_routing_rule(
        db_con, "Test", 10, "channel_title", "contains", "music", "PL1", "Music"
    )
    assert rid is not None
    rules = get_routing_rules(db_con)
    assert len(rules) == 1
    assert rules[0]["name"] == "Test"
    assert update_routing_rule(db_con, rid, name="Updated")
    assert delete_routing_rule(db_con, rid)
    assert len(get_routing_rules(db_con)) == 0


def test_pipeline_runs(db_con):
    rid = create_pipeline_run(db_con, trigger="manual")
    assert rid is not None
    summary = {
        "status": "completed",
        "videos_added": 5,
        "subscriptions_processed": 10,
        "subscriptions_skipped": 2,
        "videos_skipped": 3,
        "errors": 0,
        "error_message": "",
    }
    assert finish_pipeline_run(db_con, rid, summary)
    runs = get_pipeline_runs(db_con)
    assert len(runs) == 1
    assert runs[0]["status"] == "completed"
    assert get_pipeline_run(db_con, rid)["videos_added"] == 5


def test_app_config(db_con):
    assert get_config(db_con, "test_key") is None
    assert set_config(db_con, "test_key", "test_value")
    assert get_config(db_con, "test_key") == "test_value"
    assert set_config(db_con, "test_key", "updated")
    assert get_config(db_con, "test_key") == "updated"


# ── Pipeline sort_order / reorder tests ─────────────────────────────


def test_create_pipeline_with_sort_order(db_con):
    """create_pipeline with explicit sort_order should persist."""
    assert create_pipeline(
        db_con, "p_sort1", "Sorted", "PL_dest", "Dest", sort_order=42
    )
    pipelines = get_pipelines(db_con)
    match = [p for p in pipelines if p["id"] == "p_sort1"]
    assert len(match) == 1
    assert match[0]["sort_order"] == 42


def test_create_pipeline_auto_sort_order(db_con):
    """create_pipeline without sort_order should auto-assign max+1."""
    assert create_pipeline(db_con, "p_auto1", "First", "PL_dest", "Dest")
    assert create_pipeline(db_con, "p_auto2", "Second", "PL_dest", "Dest")
    pipelines = get_pipelines(db_con)
    p1 = [p for p in pipelines if p["id"] == "p_auto1"][0]
    p2 = [p for p in pipelines if p["id"] == "p_auto2"][0]
    # Second gets sort_order=1 (max 0 + 1)
    assert p2["sort_order"] == p1["sort_order"] + 1


def test_get_pipelines_ordered_by_sort_order(db_con):
    """get_pipelines should return pipelines ordered by sort_order ASC, name ASC."""
    assert create_pipeline(db_con, "p_c", "C Pipe", "PL_dest", "Dest", sort_order=2)
    assert create_pipeline(db_con, "p_a", "A Pipe", "PL_dest", "Dest", sort_order=0)
    assert create_pipeline(db_con, "p_b", "B Pipe", "PL_dest", "Dest", sort_order=1)
    pipelines = get_pipelines(db_con)
    order = [p["sort_order"] for p in pipelines if p["id"].startswith("p_")]
    assert order == sorted(order)


def test_reorder_pipelines_happy_path(db_con):
    """reorder_pipelines assigns sequential sort_order based on list position."""
    assert create_pipeline(db_con, "r1", "R1", "PL_dest", "Dest")
    assert create_pipeline(db_con, "r2", "R2", "PL_dest", "Dest")
    assert create_pipeline(db_con, "r3", "R3", "PL_dest", "Dest")

    assert reorder_pipelines(db_con, ["r3", "r1", "r2"])
    pipelines = get_pipelines(db_con)
    r1 = [p for p in pipelines if p["id"] == "r1"][0]
    r2 = [p for p in pipelines if p["id"] == "r2"][0]
    r3 = [p for p in pipelines if p["id"] == "r3"][0]
    assert r3["sort_order"] == 0  # first in list
    assert r1["sort_order"] == 1
    assert r2["sort_order"] == 2


def test_reorder_pipelines_non_existent_ids(db_con):
    """reorder_pipelines with non-existent IDs should not raise."""
    assert create_pipeline(db_con, "r_ex", "Exists", "PL_dest", "Dest")
    # Should not fail even though "ghost" doesn't exist
    assert reorder_pipelines(db_con, ["r_ex", "ghost"])
    pipelines = get_pipelines(db_con)
    r_ex = [p for p in pipelines if p["id"] == "r_ex"][0]
    assert r_ex["sort_order"] == 0


def test_reorder_pipelines_empty_list(db_con):
    """reorder_pipelines with empty list should succeed (no-op)."""
    assert create_pipeline(db_con, "r_empty", "EmptyTest", "PL_dest", "Dest")
    assert reorder_pipelines(db_con, [])


# ── PipelineConfig sort_order test ──────────────────────────────────


def test_pipeline_config_construction_includes_sort_order():
    """PipelineConfig construction from DB dict should include sort_order."""
    from sortarr.models.pipeline import PipelineConfig

    p = PipelineConfig(
        id="test",
        name="Test",
        destination_playlist_id="PL_dest",
        destination_playlist_title="Dest",
        sort_order=7,
    )
    assert p.sort_order == 7


def test_ignore_entries(db_con):
    assert get_ignore_entries(db_con, "subscription") == []
    eid = add_ignore_entry(db_con, "subscription", "test-channel")
    assert eid is not None
    entries = get_ignore_entries(db_con, "subscription")
    assert len(entries) == 1
    assert entries[0]["pattern"] == "test-channel"
    assert update_ignore_entry(db_con, eid, "updated-channel")
    entries = get_ignore_entries(db_con, "subscription")
    assert entries[0]["pattern"] == "updated-channel"
    assert delete_ignore_entry(db_con, eid)
    assert get_ignore_entries(db_con, "subscription") == []
