"""Unit tests for pipelines repository."""

import sqlite3
from pathlib import Path

import pytest

from sortarr.db import migrations
from sortarr.db.connection import init_db, close_db
from sortarr.db.repository import pipelines
from sortarr.models.pipeline import PipelineCreate, PipelineUpdate


@pytest.fixture
def test_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    conn = init_db(str(db_path))
    migrations.init_db(conn)
    yield conn
    close_db()


def test_create_pipeline_basic(test_db):
    """Test creating a basic pipeline."""
    config = PipelineCreate(
        name="Test Pipeline",
        playlist_id="PLtest123",
        subscription_scope="all",
        selector_mode="AND",
    )
    
    result = pipelines.create_pipeline(config)
    
    assert result.id is not None
    assert result.name == "Test Pipeline"
    assert result.playlist_id == "PLtest123"
    assert result.enabled is True
    assert result.order == 0
    assert result.subscription_scope == "all"
    assert result.selector_mode == "AND"


def test_create_pipeline_with_ignore_lists(test_db):
    """Test creating a pipeline with ignore lists."""
    # First create some ignore lists
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ignore1", "Test Ignore 1", "word"),
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ignore2", "Test Ignore 2", "video"),
    )
    test_db.commit()
    
    config = PipelineCreate(
        name="Pipeline with Ignores",
        playlist_id="PLtest456",
        ignore_list_ids=["ignore1", "ignore2"],
    )
    
    result = pipelines.create_pipeline(config)
    
    assert result.id is not None
    assert result.name == "Pipeline with Ignores"
    
    # Verify junction table entries
    ignore_ids = pipelines.get_pipeline_ignore_lists(result.id)
    assert set(ignore_ids) == {"ignore1", "ignore2"}


def test_create_pipeline_with_selectors(test_db):
    """Test creating a pipeline with selectors."""
    config = PipelineCreate(
        name="Pipeline with Selectors",
        playlist_id="PLtest789",
        selector_ids=["sel1", "sel2", "sel3"],
    )
    
    result = pipelines.create_pipeline(config)
    
    assert result.id is not None
    
    # Verify junction table entries
    selector_ids = pipelines.get_pipeline_selectors(result.id)
    assert set(selector_ids) == {"sel1", "sel2", "sel3"}


def test_create_pipeline_with_subscriptions(test_db):
    """Test creating a pipeline with subscription scope."""
    # First create some subscriptions
    test_db.execute(
        "INSERT INTO subscriptions (id, title, channel_id, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("sub1", "Channel 1", "UC123"),
    )
    test_db.execute(
        "INSERT INTO subscriptions (id, title, channel_id, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("sub2", "Channel 2", "UC456"),
    )
    test_db.commit()
    
    config = PipelineCreate(
        name="Pipeline with Subs",
        playlist_id="PLtestABC",
        subscription_scope="selected",
        subscription_ids=["sub1", "sub2"],
    )
    
    result = pipelines.create_pipeline(config)
    
    assert result.id is not None
    assert result.subscription_scope == "selected"
    
    # Verify junction table entries
    sub_ids = pipelines.get_pipeline_subscriptions(result.id)
    assert set(sub_ids) == {"sub1", "sub2"}


def test_get_pipeline_exists(test_db):
    """Test getting an existing pipeline."""
    config = PipelineCreate(name="Get Test", playlist_id="PLget123")
    created = pipelines.create_pipeline(config)
    
    result = pipelines.get_pipeline(created.id)
    
    assert result.id == created.id
    assert result.name == "Get Test"
    assert result.playlist_id == "PLget123"


def test_get_pipeline_not_exists(test_db):
    """Test getting a non-existent pipeline raises ValueError."""
    with pytest.raises(ValueError, match="pipeline not found"):
        pipelines.get_pipeline("nonexistent-id")


def test_list_pipelines_empty(test_db):
    """Test listing pipelines when none exist."""
    result = pipelines.list_pipelines()
    assert result == []


def test_list_pipelines_multiple(test_db):
    """Test listing multiple pipelines."""
    p1 = pipelines.create_pipeline(PipelineCreate(name="Pipeline 1", playlist_id="PL1"))
    p2 = pipelines.create_pipeline(PipelineCreate(name="Pipeline 2", playlist_id="PL2"))
    p3 = pipelines.create_pipeline(PipelineCreate(name="Pipeline 3", playlist_id="PL3"))
    
    result = pipelines.list_pipelines()
    
    assert len(result) == 3
    assert {p.id for p in result} == {p1.id, p2.id, p3.id}
    # Should be ordered by sort_order, then name
    assert result[0].name == "Pipeline 1"


def test_update_pipeline_partial(test_db):
    """Test partial update of a pipeline."""
    created = pipelines.create_pipeline(
        PipelineCreate(name="Original Name", playlist_id="PLoriginal")
    )
    
    updates = PipelineUpdate(name="Updated Name", enabled=False)
    result = pipelines.update_pipeline(created.id, updates)
    
    assert result.id == created.id
    assert result.name == "Updated Name"
    assert result.enabled is False
    assert result.playlist_id == "PLoriginal"  # unchanged


def test_update_pipeline_all_fields(test_db):
    """Test updating all fields of a pipeline."""
    created = pipelines.create_pipeline(
        PipelineCreate(
            name="Original",
            playlist_id="PLoriginal",
            subscription_scope="all",
            duration_min_seconds=60,
            duration_max_seconds=600,
            selector_mode="AND",
        )
    )
    
    updates = PipelineUpdate(
        name="Updated",
        enabled=False,
        playlist_id="PLupdated",
        order=5,
        subscription_scope="selected",
        duration_min_seconds=120,
        duration_max_seconds=1200,
        selector_mode="OR",
    )
    result = pipelines.update_pipeline(created.id, updates)
    
    assert result.name == "Updated"
    assert result.enabled is False
    assert result.playlist_id == "PLupdated"
    assert result.order == 5
    assert result.subscription_scope == "selected"
    assert result.duration_min_seconds == 120
    assert result.duration_max_seconds == 1200
    assert result.selector_mode == "OR"


def test_delete_pipeline(test_db):
    """Test deleting a pipeline."""
    created = pipelines.create_pipeline(PipelineCreate(name="To Delete", playlist_id="PLdel"))
    
    pipelines.delete_pipeline(created.id)
    
    with pytest.raises(ValueError, match="pipeline not found"):
        pipelines.get_pipeline(created.id)


def test_delete_pipeline_cascade_ignore_lists(test_db):
    """Test that deleting a pipeline cascades to junction tables."""
    # Create ignore lists
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ignore1", "Test Ignore", "word"),
    )
    test_db.commit()
    
    # Create pipeline with ignore list
    created = pipelines.create_pipeline(
        PipelineCreate(name="Cascade Test", playlist_id="PLcascade", ignore_list_ids=["ignore1"])
    )
    
    # Verify junction entry exists
    assert pipelines.get_pipeline_ignore_lists(created.id) == ["ignore1"]
    
    # Delete pipeline
    pipelines.delete_pipeline(created.id)
    
    # Verify junction entry was cascade deleted
    rows = test_db.execute(
        "SELECT * FROM pipeline_ignore_lists WHERE pipeline_id = ?", (created.id,)
    ).fetchall()
    assert len(rows) == 0


def test_delete_pipeline_cascade_selectors(test_db):
    """Test that deleting a pipeline cascades to selectors."""
    created = pipelines.create_pipeline(
        PipelineCreate(name="Selector Cascade", playlist_id="PLsel", selector_ids=["sel1", "sel2"])
    )
    
    # Verify selectors exist
    assert len(pipelines.get_pipeline_selectors(created.id)) == 2
    
    # Delete pipeline
    pipelines.delete_pipeline(created.id)
    
    # Verify selectors were cascade deleted
    rows = test_db.execute(
        "SELECT * FROM pipeline_selectors WHERE pipeline_id = ?", (created.id,)
    ).fetchall()
    assert len(rows) == 0


def test_delete_pipeline_cascade_subscriptions(test_db):
    """Test that deleting a pipeline cascades to subscription junction."""
    # Create subscription
    test_db.execute(
        "INSERT INTO subscriptions (id, title, channel_id, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("sub1", "Channel", "UC123"),
    )
    test_db.commit()
    
    created = pipelines.create_pipeline(
        PipelineCreate(
            name="Sub Cascade",
            playlist_id="PLsub",
            subscription_scope="selected",
            subscription_ids=["sub1"],
        )
    )
    
    # Verify subscription link exists
    assert pipelines.get_pipeline_subscriptions(created.id) == ["sub1"]
    
    # Delete pipeline
    pipelines.delete_pipeline(created.id)
    
    # Verify subscription link was cascade deleted
    rows = test_db.execute(
        "SELECT * FROM pipeline_subscriptions WHERE pipeline_id = ?", (created.id,)
    ).fetchall()
    assert len(rows) == 0


def test_reorder_pipelines(test_db):
    """Test reordering pipelines."""
    p1 = pipelines.create_pipeline(PipelineCreate(name="First", playlist_id="PL1"))
    p2 = pipelines.create_pipeline(PipelineCreate(name="Second", playlist_id="PL2"))
    p3 = pipelines.create_pipeline(PipelineCreate(name="Third", playlist_id="PL3"))
    
    # Reorder: p3, p1, p2
    pipelines.reorder_pipelines([p3.id, p1.id, p2.id])
    
    # Verify new order
    result = pipelines.list_pipelines()
    assert result[0].id == p3.id
    assert result[0].order == 0
    assert result[1].id == p1.id
    assert result[1].order == 1
    assert result[2].id == p2.id
    assert result[2].order == 2


def test_set_and_get_ignore_lists(test_db):
    """Test setting and getting ignore lists for a pipeline."""
    # Create ignore lists
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ig1", "Ignore 1", "word"),
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ig2", "Ignore 2", "video"),
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("ig3", "Ignore 3", "subscription"),
    )
    test_db.commit()
    
    created = pipelines.create_pipeline(PipelineCreate(name="Test", playlist_id="PL1"))
    
    # Set ignore lists
    pipelines.set_ignore_lists(created.id, ["ig1", "ig2"])
    assert set(pipelines.get_pipeline_ignore_lists(created.id)) == {"ig1", "ig2"}
    
    # Replace ignore lists
    pipelines.set_ignore_lists(created.id, ["ig3"])
    assert pipelines.get_pipeline_ignore_lists(created.id) == ["ig3"]
    
    # Clear ignore lists
    pipelines.set_ignore_lists(created.id, [])
    assert pipelines.get_pipeline_ignore_lists(created.id) == []


def test_set_and_get_selectors(test_db):
    """Test setting and getting selectors for a pipeline."""
    created = pipelines.create_pipeline(PipelineCreate(name="Test", playlist_id="PL1"))
    
    # Set selectors
    pipelines.set_selectors(created.id, ["sel1", "sel2", "sel3"])
    assert set(pipelines.get_pipeline_selectors(created.id)) == {"sel1", "sel2", "sel3"}
    
    # Replace selectors
    pipelines.set_selectors(created.id, ["sel4"])
    assert pipelines.get_pipeline_selectors(created.id) == ["sel4"]
    
    # Clear selectors
    pipelines.set_selectors(created.id, [])
    assert pipelines.get_pipeline_selectors(created.id) == []


def test_set_and_get_subscriptions(test_db):
    """Test setting and getting subscriptions for a pipeline."""
    # Create subscriptions
    test_db.execute(
        "INSERT INTO subscriptions (id, title, channel_id, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("sub1", "Channel 1", "UC1"),
    )
    test_db.execute(
        "INSERT INTO subscriptions (id, title, channel_id, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("sub2", "Channel 2", "UC2"),
    )
    test_db.commit()
    
    created = pipelines.create_pipeline(PipelineCreate(name="Test", playlist_id="PL1"))
    
    # Set subscriptions
    pipelines.set_subscriptions(created.id, ["sub1", "sub2"])
    assert set(pipelines.get_pipeline_subscriptions(created.id)) == {"sub1", "sub2"}
    
    # Replace subscriptions
    pipelines.set_subscriptions(created.id, ["sub1"])
    assert pipelines.get_pipeline_subscriptions(created.id) == ["sub1"]
    
    # Clear subscriptions
    pipelines.set_subscriptions(created.id, [])
    assert pipelines.get_pipeline_subscriptions(created.id) == []


def test_create_pipeline_with_duration_filters(test_db):
    """Test creating a pipeline with duration filters."""
    config = PipelineCreate(
        name="Duration Pipeline",
        playlist_id="PLdur",
        duration_min_seconds=120,
        duration_max_seconds=600,
    )
    
    result = pipelines.create_pipeline(config)
    
    assert result.duration_min_seconds == 120
    assert result.duration_max_seconds == 600


def test_parameterized_queries_no_sql_injection(test_db):
    """Test that queries are properly parameterized (no SQL injection)."""
    # Try to inject SQL via name field
    malicious_name = "Test'; DROP TABLE pipelines; --"
    
    config = PipelineCreate(name=malicious_name, playlist_id="PLtest")
    result = pipelines.create_pipeline(config)
    
    # Should succeed without executing the injection
    assert result.name == malicious_name
    
    # Verify table still exists
    rows = test_db.execute("SELECT COUNT(*) as count FROM pipelines").fetchone()
    assert rows["count"] == 1
