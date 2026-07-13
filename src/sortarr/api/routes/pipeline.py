"""sortarr.api.routes.pipeline — single pipeline run management routes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status

from sortarr.api.deps import get_runner, get_state
from sortarr.db.repository import config, runs
from sortarr.models.pipeline import (
    PreviewRequest,
    RunDecisionResponse,
    RunSummaryResponse,
)

if TYPE_CHECKING:
    from sortarr.api.app import AppState
    from sortarr.core.runner import Runner

log = logging.getLogger("sortarr.api.routes.pipeline")

router = APIRouter(tags=["pipeline"])


@router.post("/run", response_model=RunSummaryResponse, status_code=status.HTTP_201_CREATED)
def trigger_run(
    request: PreviewRequest,
    runner: Runner = Depends(get_runner),
) -> RunSummaryResponse:
    """Trigger a live pipeline run.

    Args:
        request: Optional pipeline_id to run (None = all enabled)
        runner: Runner instance from dependency injection

    Returns:
        RunSummaryResponse: Created run summary

    Raises:
        HTTPException: 409 if another run is already active
    """
    # Check if run is already active
    if config.get_config_value("run_active"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another run is already active",
        )

    # Execute the run
    run_id = runner.execute(mode="run", pipeline_id=request.pipeline_id)
    log.info("triggered run %d", run_id)

    # Fetch and return the run summary
    run_summary = runs.get_run(run_id)
    if not run_summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Run created but could not be retrieved",
        )

    return run_summary


@router.get("/runs", response_model=list[RunSummaryResponse])
def list_runs(limit: int = 50, state: AppState = Depends(get_state)) -> list[RunSummaryResponse]:
    """List run history.

    Args:
        limit: Maximum number of runs to return (default 50)
        state: Application state from dependency injection

    Returns:
        List of run summaries, ordered by started_at DESC
    """
    return runs.list_runs(limit=limit)


@router.get("/runs/{run_id}", response_model=RunSummaryResponse)
def get_run(run_id: int, state: AppState = Depends(get_state)) -> RunSummaryResponse:
    """Get a single run by ID.

    Args:
        run_id: Run ID
        state: Application state from dependency injection

    Returns:
        Run summary

    Raises:
        HTTPException: 404 if run not found
    """
    run_summary = runs.get_run(run_id)
    if not run_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )
    return run_summary


@router.get("/runs/{run_id}/decisions", response_model=list[RunDecisionResponse])
def get_run_decisions(
    run_id: int,
    limit: int = 500,
    state: AppState = Depends(get_state),
) -> list[RunDecisionResponse]:
    """Get decisions for a run.

    Args:
        run_id: Run ID
        limit: Maximum number of decisions to return (default 500)
        state: Application state from dependency injection

    Returns:
        List of run decisions (inserted/skipped per video)

    Raises:
        HTTPException: 404 if run not found
    """
    # Verify run exists
    run_summary = runs.get_run(run_id)
    if not run_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )

    return runs.get_decisions(run_id, limit=limit)
