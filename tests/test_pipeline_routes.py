"""Tests for sortarr.api.routes.pipelines — Pipeline CRUD routes."""

import sqlite3
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from sortarr.api.app import create_app
from sortarr.db.connection import close_db, init_db
from sortarr.db.migrations import init_db as apply_schema


@pytest.fixture
def test_db(tmp_path: Path):
    """Create a test database."""
    db_path = tmp_path / "test.db"
    conn = init_db(str(db_path))
    apply_schema(conn)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    yield conn
    close_db()


@pytest.fixture
async def client(test_db: sqlite3.Connection):
    """Create test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# List pipelines tests


async def test_list_pipelines_empty(client: AsyncClient):
    """Test listing pipelines when none exist."""
    response = await client.get("/api/pipelines")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_pipelines_ordered(client: AsyncClient, test_db: sqlite3.Connection):
    """Test pipelines are returned in sort_order, then name order."""
    # Create pipelines with different sort orders
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES
        ('p1', 'Pipeline A', 1, 'pl1', '', 'AND', 'all', 0, 0, 2, datetime('now'), datetime('now')),
        ('p2', 'Pipeline B', 1, 'pl2', '', 'AND', 'all', 0, 0, 1, datetime('now'), datetime('now')),
        ('p3', 'Pipeline C', 1, 'pl3', '', 'AND', 'all', 0, 0, 1, datetime('now'), datetime('now'))
    """
    )
    test_db.commit()

    response = await client.get("/api/pipelines")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Should be ordered by sort_order (1, 1, 2), then name (B, C, A)
    assert data[0]["name"] == "Pipeline B"
    assert data[1]["name"] == "Pipeline C"
    assert data[2]["name"] == "Pipeline A"


# Get single pipeline tests


async def test_get_pipeline_success(client: AsyncClient, test_db: sqlite3.Connection):
    """Test getting a single pipeline by ID."""
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'Test Pipeline', 1, 'pl1', 'My Playlist', 'AND', 'all', 60, 3600, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.commit()

    response = await client.get("/api/pipelines/p1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "p1"
    assert data["name"] == "Test Pipeline"
    assert data["enabled"] is True
    assert data["playlist_id"] == "pl1"
    assert data["duration_min_seconds"] == 60
    assert data["duration_max_seconds"] == 3600


async def test_get_pipeline_not_found(client: AsyncClient):
    """Test getting a non-existent pipeline returns 404."""
    response = await client.get("/api/pipelines/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# Create pipeline tests


async def test_create_pipeline_minimal(client: AsyncClient):
    """Test creating a pipeline with minimal fields."""
    payload = {
        "name": "New Pipeline",
        "playlist_id": "PLtest123",
    }
    response = await client.post("/api/pipelines", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Pipeline"
    assert data["playlist_id"] == "PLtest123"
    assert data["enabled"] is True
    assert data["subscription_scope"] == "all"
    assert data["selector_mode"] == "AND"
    assert "id" in data


async def test_create_pipeline_with_junction_tables(client: AsyncClient, test_db: sqlite3.Connection):
    """Test creating a pipeline with ignore lists and subscriptions."""
    # Create ignore lists and subscriptions first
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES ('il1', 'List 1', 'word', datetime('now'))"
    )
    test_db.execute(
        "INSERT INTO subscriptions (id, title, channel_id, created_at) VALUES ('sub1', 'Channel 1', 'ch1', datetime('now'))"
    )
    test_db.commit()

    payload = {
        "name": "Pipeline with Junctions",
        "playlist_id": "PLtest456",
        "ignore_list_ids": ["il1"],
        "subscription_ids": ["sub1"],
    }
    response = await client.post("/api/pipelines", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["ignore_list_ids"] == ["il1"]
    assert data["subscription_ids"] == ["sub1"]


async def test_create_pipeline_empty_playlist_id_rejected(client: AsyncClient):
    """Test creating a pipeline with empty playlist_id is rejected."""
    payload = {
        "name": "Bad Pipeline",
        "playlist_id": "",
    }
    response = await client.post("/api/pipelines", json=payload)
    assert response.status_code == 400
    assert "playlist_id" in response.json()["detail"]


# Update pipeline tests


async def test_update_pipeline_partial(client: AsyncClient, test_db: sqlite3.Connection):
    """Test partial update of a pipeline."""
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'Original', 1, 'pl1', '', 'AND', 'all', 0, 0, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.commit()

    payload = {"name": "Updated", "enabled": False}
    response = await client.put("/api/pipelines/p1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["enabled"] is False
    assert data["playlist_id"] == "pl1"  # Unchanged


async def test_update_pipeline_not_found(client: AsyncClient):
    """Test updating a non-existent pipeline returns 404."""
    payload = {"name": "Updated"}
    response = await client.put("/api/pipelines/nonexistent", json=payload)
    assert response.status_code == 404


# Delete pipeline tests


async def test_delete_pipeline_success(client: AsyncClient, test_db: sqlite3.Connection):
    """Test deleting a pipeline."""
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'To Delete', 1, 'pl1', '', 'AND', 'all', 0, 0, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.commit()

    response = await client.delete("/api/pipelines/p1")
    assert response.status_code == 204

    # Verify it's gone
    row = test_db.execute("SELECT id FROM pipelines WHERE id = 'p1'").fetchone()
    assert row is None


async def test_delete_pipeline_cascade(client: AsyncClient, test_db: sqlite3.Connection):
    """Test deleting a pipeline cascades to junction tables."""
    # Create pipeline with junction table entries
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'Pipeline', 1, 'pl1', '', 'AND', 'all', 0, 0, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES ('il1', 'List', 'word', datetime('now'))"
    )
    test_db.execute(
        "INSERT INTO pipeline_ignore_lists (pipeline_id, ignore_list_id) VALUES ('p1', 'il1')"
    )
    test_db.commit()

    response = await client.delete("/api/pipelines/p1")
    assert response.status_code == 204

    # Verify junction table entry is gone
    row = test_db.execute(
        "SELECT * FROM pipeline_ignore_lists WHERE pipeline_id = 'p1'"
    ).fetchone()
    assert row is None


# Reorder pipelines tests


async def test_reorder_pipelines(client: AsyncClient, test_db: sqlite3.Connection):
    """Test reordering pipelines."""
    # Create pipelines
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES
        ('p1', 'A', 1, 'pl1', '', 'AND', 'all', 0, 0, 0, datetime('now'), datetime('now')),
        ('p2', 'B', 1, 'pl2', '', 'AND', 'all', 0, 0, 1, datetime('now'), datetime('now')),
        ('p3', 'C', 1, 'pl3', '', 'AND', 'all', 0, 0, 2, datetime('now'), datetime('now'))
    """
    )
    test_db.commit()

    payload = {"pipeline_ids": ["p3", "p1", "p2"]}
    response = await client.put("/api/pipelines/reorder", json=payload)
    assert response.status_code == 204

    # Verify new order
    rows = test_db.execute(
        "SELECT id, sort_order FROM pipelines ORDER BY sort_order"
    ).fetchall()
    assert rows[0]["id"] == "p3"
    assert rows[0]["sort_order"] == 0
    assert rows[1]["id"] == "p1"
    assert rows[1]["sort_order"] == 1
    assert rows[2]["id"] == "p2"
    assert rows[2]["sort_order"] == 2


# Junction table tests


async def test_set_ignore_lists(client: AsyncClient, test_db: sqlite3.Connection):
    """Test setting ignore lists for a pipeline."""
    # Create pipeline and ignore lists
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'Pipeline', 1, 'pl1', '', 'AND', 'all', 0, 0, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES ('il1', 'List 1', 'word', datetime('now'))"
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES ('il2', 'List 2', 'word', datetime('now'))"
    )
    test_db.commit()

    payload = {"ids": ["il1", "il2"]}
    response = await client.put("/api/pipelines/p1/ignore-lists", json=payload)
    assert response.status_code == 204

    # Verify associations
    rows = test_db.execute(
        "SELECT ignore_list_id FROM pipeline_ignore_lists WHERE pipeline_id = 'p1' ORDER BY ignore_list_id"
    ).fetchall()
    assert len(rows) == 2
    assert rows[0]["ignore_list_id"] == "il1"
    assert rows[1]["ignore_list_id"] == "il2"


async def test_set_ignore_lists_replaces_existing(client: AsyncClient, test_db: sqlite3.Connection):
    """Test setting ignore lists replaces existing associations."""
    # Create pipeline with existing association
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'Pipeline', 1, 'pl1', '', 'AND', 'all', 0, 0, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES ('il1', 'List 1', 'word', datetime('now'))"
    )
    test_db.execute(
        "INSERT INTO ignore_lists (id, name, list_type, created_at) VALUES ('il2', 'List 2', 'word', datetime('now'))"
    )
    test_db.execute(
        "INSERT INTO pipeline_ignore_lists (pipeline_id, ignore_list_id) VALUES ('p1', 'il1')"
    )
    test_db.commit()

    # Replace with new list
    payload = {"ids": ["il2"]}
    response = await client.put("/api/pipelines/p1/ignore-lists", json=payload)
    assert response.status_code == 204

    # Verify only il2 is associated
    rows = test_db.execute(
        "SELECT ignore_list_id FROM pipeline_ignore_lists WHERE pipeline_id = 'p1'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["ignore_list_id"] == "il2"


async def test_set_subscriptions(client: AsyncClient, test_db: sqlite3.Connection):
    """Test setting subscriptions for a pipeline."""
    # Create pipeline and subscriptions
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'Pipeline', 1, 'pl1', '', 'AND', 'selected', 0, 0, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.execute(
        "INSERT INTO subscriptions (id, title, channel_id, created_at) VALUES ('sub1', 'Ch1', 'ch1', datetime('now'))"
    )
    test_db.commit()

    payload = {"ids": ["sub1"]}
    response = await client.put("/api/pipelines/p1/subscriptions", json=payload)
    assert response.status_code == 204

    # Verify association
    rows = test_db.execute(
        "SELECT subscription_id FROM pipeline_subscriptions WHERE pipeline_id = 'p1'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["subscription_id"] == "sub1"


async def test_set_selectors_not_implemented(client: AsyncClient, test_db: sqlite3.Connection):
    """Test setting selectors returns 501 (not implemented)."""
    test_db.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES ('p1', 'Pipeline', 1, 'pl1', '', 'AND', 'all', 0, 0, 0, datetime('now'), datetime('now'))
    """
    )
    test_db.commit()

    payload = {"ids": ["sel1"]}
    response = await client.put("/api/pipelines/p1/selectors", json=payload)
    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"].lower()

