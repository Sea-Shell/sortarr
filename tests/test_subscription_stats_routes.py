"""Tests for sortarr.api.routes.subscriptions and stats — Subscription and stats routes."""

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


# GET /api/subscriptions tests


async def test_list_subscriptions_empty(client: AsyncClient):
    """Test listing subscriptions when none exist."""
    response = await client.get("/api/subscriptions")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_subscriptions(client: AsyncClient, test_db: sqlite3.Connection):
    """Test listing subscriptions."""
    test_db.execute("""
        INSERT INTO subscriptions (id, channel_id, title, created_at) VALUES
        ('sub1', 'ch1', 'Channel A', datetime('now')),
        ('sub2', 'ch2', 'Channel B', datetime('now'))
    """)
    test_db.commit()

    response = await client.get("/api/subscriptions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["channel_title"] == "Channel A"


# GET /api/subscriptions/stats tests


async def test_subscription_stats_empty(client: AsyncClient):
    """Test subscription stats when none exist."""
    response = await client.get("/api/subscriptions/stats")
    assert response.status_code == 200
    assert response.json() == []


# GET /api/playlists tests


async def test_list_playlists_requires_auth(client: AsyncClient):
    """Test listing playlists without authentication returns 401."""
    response = await client.get("/api/playlists")
    assert response.status_code == 401


# GET /api/stats tests


async def test_dashboard_stats_empty(client: AsyncClient):
    """Test dashboard stats with empty database."""
    response = await client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["pipelines_count"] == 0
    assert data["subscriptions_count"] == 0
