"""Tests for sortarr.api.routes.preview — Preview routes."""

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


async def test_mock_preview_returns_empty(client: AsyncClient):
    """Test mock preview returns empty list (not implemented yet)."""
    response = await client.post("/api/preview/mock", json={"pipeline_id": None})
    assert response.status_code == 200
    assert response.json() == []


async def test_cache_preview_returns_empty(client: AsyncClient):
    """Test cache preview returns empty list (not implemented yet)."""
    response = await client.post("/api/preview/cache", json={"pipeline_id": None})
    assert response.status_code == 200
    assert response.json() == []
