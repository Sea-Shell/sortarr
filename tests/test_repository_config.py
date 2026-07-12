"""Unit tests for sortarr.db.repository.config"""

import pytest
from sortarr.db.connection import init_db, close_db
from sortarr.db.migrations import init_db as apply_schema
from sortarr.db.repository import config


@pytest.fixture
def db():
    """Initialize an in-memory database for testing."""
    conn = init_db(":memory:")
    apply_schema(conn)
    yield conn
    close_db()


def test_get_config_empty(db):
    """Test get_config returns empty dict when no config exists."""
    result = config.get_config()
    assert result == {}


def test_set_and_get_config(db):
    """Test setting and getting a config value."""
    config.set_config("test_key", "test_value")
    result = config.get_config_value("test_key")
    assert result == "test_value"


def test_set_config_upsert(db):
    """Test that set_config upserts (updates existing key)."""
    config.set_config("key1", "value1")
    config.set_config("key1", "value2")
    result = config.get_config_value("key1")
    assert result == "value2"


def test_get_config_value_default(db):
    """Test get_config_value returns default when key doesn't exist."""
    result = config.get_config_value("nonexistent", default="default_value")
    assert result == "default_value"


def test_get_config_value_none_default(db):
    """Test get_config_value returns None when key doesn't exist and no default."""
    result = config.get_config_value("nonexistent")
    assert result is None


def test_get_config_multiple(db):
    """Test get_config returns all key-value pairs."""
    config.set_config("key1", "value1")
    config.set_config("key2", "value2")
    config.set_config("key3", "value3")
    
    result = config.get_config()
    assert result == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }


def test_config_parameterized_queries(db):
    """Test that queries are parameterized (SQL injection safe)."""
    # Try to inject SQL
    malicious_key = "key'; DROP TABLE app_config; --"
    config.set_config(malicious_key, "value")
    
    # Should store the literal string, not execute SQL
    result = config.get_config_value(malicious_key)
    assert result == "value"
    
    # Table should still exist
    all_config = config.get_config()
    assert malicious_key in all_config
