"""Unit tests for sortarr.db.repository.subscriptions"""

import pytest
from sortarr.db.connection import init_db, close_db
from sortarr.db.migrations import init_db as apply_schema
from sortarr.db.repository import subscriptions
from sortarr.models.youtube import Subscription


@pytest.fixture
def db():
    """Initialize an in-memory database for testing."""
    conn = init_db(":memory:")
    apply_schema(conn)
    yield conn
    close_db()


def test_upsert_and_list_subscriptions(db):
    """Test upserting and listing subscriptions."""
    subs = [
        Subscription(
            subscription_id="sub1",
            channel_id="ch1",
            channel_title="Channel 1"
        ),
        Subscription(
            subscription_id="sub2",
            channel_id="ch2",
            channel_title="Channel 2"
        )
    ]
    
    subscriptions.upsert_subscriptions(subs)
    result = subscriptions.list_subscriptions()
    
    assert len(result) == 2
    titles = {s.channel_title for s in result}
    assert titles == {"Channel 1", "Channel 2"}


def test_upsert_subscriptions_update(db):
    """Test that upsert updates existing subscriptions."""
    sub1 = Subscription(
        subscription_id="sub1",
        channel_id="ch1",
        channel_title="Old Title"
    )
    subscriptions.upsert_subscriptions([sub1])
    
    sub1_updated = Subscription(
        subscription_id="sub1",
        channel_id="ch1",
        channel_title="New Title"
    )
    subscriptions.upsert_subscriptions([sub1_updated])
    
    result = subscriptions.list_subscriptions()
    assert len(result) == 1
    assert result[0].channel_title == "New Title"


def test_upsert_subscriptions_empty(db):
    """Test upsert_subscriptions handles empty list."""
    subscriptions.upsert_subscriptions([])
    result = subscriptions.list_subscriptions()
    assert len(result) == 0


def test_get_subscription_stats(db):
    """Test getting subscription statistics."""
    subs = [
        Subscription(subscription_id=f"sub{i}", channel_id=f"ch{i}", channel_title=f"Ch{i}")
        for i in range(5)
    ]
    subscriptions.upsert_subscriptions(subs)
    
    stats = subscriptions.get_subscription_stats()
    assert stats["count"] == 5


def test_update_and_get_tracking(db):
    """Test updating and retrieving subscription tracking."""
    subscriptions.update_tracking("sub1", "2024-01-01T00:00:00Z")
    
    tracking = subscriptions.get_tracking("sub1")
    assert tracking is not None
    assert tracking["last_fetched_at"] == "2024-01-01T00:00:00Z"


def test_update_tracking_upsert(db):
    """Test that update_tracking upserts."""
    subscriptions.update_tracking("sub1", "2024-01-01T00:00:00Z")
    subscriptions.update_tracking("sub1", "2024-01-02T00:00:00Z")
    
    tracking = subscriptions.get_tracking("sub1")
    assert tracking is not None
    assert tracking["last_fetched_at"] == "2024-01-02T00:00:00Z"


def test_get_tracking_nonexistent(db):
    """Test get_tracking returns None for nonexistent subscription."""
    tracking = subscriptions.get_tracking("nonexistent")
    assert tracking is None


def test_subscriptions_parameterized_queries(db):
    """Test that queries are parameterized (SQL injection safe)."""
    malicious_id = "sub'; DROP TABLE subscriptions; --"
    sub = Subscription(
        subscription_id=malicious_id,
        channel_id="ch1",
        channel_title="Test"
    )
    
    subscriptions.upsert_subscriptions([sub])
    result = subscriptions.list_subscriptions()
    assert len(result) == 1
    assert result[0].subscription_id == malicious_id
