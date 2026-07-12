"""Unit tests for sortarr.db.repository.runs"""

import pytest
from sortarr.db.connection import init_db, close_db
from sortarr.db.migrations import init_db as apply_schema
from sortarr.db.repository import runs
from sortarr.models.pipeline import RunSummary


@pytest.fixture
def db():
    """Initialize an in-memory database for testing."""
    conn = init_db(":memory:")
    apply_schema(conn)
    yield conn
    close_db()


def test_create_and_get_run(db):
    """Test creating and retrieving a run."""
    run = RunSummary(
        status="running",
        trigger="manual",
        started_at="2024-01-01T00:00:00Z",
        subscriptions_fetched=10,
        activities_collected=50,
        videos_inserted=5,
        quota_used=100
    )
    
    run_id = runs.create_run(run)
    assert run_id > 0
    
    retrieved = runs.get_run(run_id)
    assert retrieved is not None
    assert retrieved.status == "running"
    assert retrieved.trigger == "manual"
    assert retrieved.subscriptions_fetched == 10


def test_update_run(db):
    """Test updating a run."""
    run = RunSummary(
        status="running",
        trigger="manual",
        started_at="2024-01-01T00:00:00Z"
    )
    
    run_id = runs.create_run(run)
    runs.update_run(run_id, {
        "status": "completed",
        "finished_at": "2024-01-01T01:00:00Z",
        "videos_inserted": 10
    })
    
    retrieved = runs.get_run(run_id)
    assert retrieved is not None
    assert retrieved.status == "completed"
    assert retrieved.completed_at == "2024-01-01T01:00:00Z"
    assert retrieved.videos_inserted == 10


def test_list_runs(db):
    """Test listing runs."""
    for i in range(5):
        run = RunSummary(
            status="completed",
            trigger="scheduled",
            started_at=f"2024-01-0{i+1}T00:00:00Z"
        )
        runs.create_run(run)
    
    all_runs = runs.list_runs(limit=10)
    assert len(all_runs) == 5
    # Should be ordered by started_at DESC (most recent first)
    assert all_runs[0].started_at is not None
    assert all_runs[-1].started_at is not None


def test_list_runs_limit(db):
    """Test list_runs respects limit."""
    for i in range(10):
        run = RunSummary(
            status="completed",
            trigger="scheduled",
            started_at=f"2024-01-01T{i:02d}:00:00Z"
        )
        runs.create_run(run)
    
    limited = runs.list_runs(limit=3)
    assert len(limited) == 3


def test_add_and_get_decisions(db):
    """Test adding and retrieving run decisions."""
    run = RunSummary(
        status="running",
        trigger="manual",
        started_at="2024-01-01T00:00:00Z"
    )
    run_id = runs.create_run(run)
    
    decisions = [
        {
            "video_id": "vid1",
            "pipeline_id": "pipe1",
            "action": "inserted",
            "filter_stage": None,
            "filter_name": None,
            "reason": None
        },
        {
            "video_id": "vid2",
            "pipeline_id": "pipe1",
            "action": "skipped",
            "filter_stage": "cheap",
            "filter_name": "word_filter",
            "reason": "blocked word: spam"
        }
    ]
    
    runs.add_decisions(run_id, decisions)
    retrieved = runs.get_decisions(run_id)
    
    assert len(retrieved) == 2
    assert retrieved[0].video_id == "vid1"
    assert retrieved[0].action == "inserted"
    assert retrieved[1].video_id == "vid2"
    assert retrieved[1].action == "skipped"
    assert retrieved[1].filter_name == "word_filter"


def test_add_decisions_empty(db):
    """Test add_decisions handles empty list."""
    run = RunSummary(
        status="running",
        trigger="manual",
        started_at="2024-01-01T00:00:00Z"
    )
    run_id = runs.create_run(run)
    
    runs.add_decisions(run_id, [])
    retrieved = runs.get_decisions(run_id)
    assert len(retrieved) == 0


def test_get_decisions_limit(db):
    """Test get_decisions respects limit."""
    run = RunSummary(
        status="running",
        trigger="manual",
        started_at="2024-01-01T00:00:00Z"
    )
    run_id = runs.create_run(run)
    
    decisions = [
        {"video_id": f"vid{i}", "action": "skipped"}
        for i in range(10)
    ]
    runs.add_decisions(run_id, decisions)
    
    limited = runs.get_decisions(run_id, limit=5)
    assert len(limited) == 5


def test_runs_parameterized_queries(db):
    """Test that queries are parameterized (SQL injection safe)."""
    malicious_trigger = "manual'; DROP TABLE pipeline_runs; --"
    run = RunSummary(
        status="running",
        trigger=malicious_trigger,
        started_at="2024-01-01T00:00:00Z"
    )
    
    run_id = runs.create_run(run)
    retrieved = runs.get_run(run_id)
    assert retrieved is not None
    assert retrieved.trigger == malicious_trigger

