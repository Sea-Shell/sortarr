from typing import List
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sortarr.api.deps import get_state
from sortarr.api.models import TriggerResponse, PipelineRunResponse, RunDecisionResponse
from sortarr.core.pipeline_runner import execute_pipeline
from sortarr.db.repository import pipeline_runs as repo
import logging

log = logging.getLogger("sortarr.api.pipeline")
router = APIRouter()


class VideoSearchResult(BaseModel):
    run_id: int
    run_started_at: str
    run_status: str
    run_trigger: str
    run_dry_run: bool
    pipeline_name: str | None
    decision: RunDecisionResponse


@router.post("/pipeline/trigger")
async def trigger_pipeline(
    request: Request, dry_run: bool = False, pipeline_id: str | None = None
):
    state = get_state(request)
    run_id = await execute_pipeline(
        state, trigger="manual", dry_run=dry_run, pipeline_id=pipeline_id
    )
    if not run_id:
        raise HTTPException(status_code=500, detail="Pipeline run failed")
    return TriggerResponse(run_id=run_id)


@router.get("/pipeline/runs", response_model=List[PipelineRunResponse])
async def list_runs(request: Request):
    state = get_state(request)
    runs = repo.get_pipeline_runs(state.db_con)
    return [PipelineRunResponse(**r) for r in runs]


@router.get("/pipeline/runs/{run_id}", response_model=PipelineRunResponse)
async def get_run(run_id: int, request: Request):
    state = get_state(request)
    run = repo.get_pipeline_run(state.db_con, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return PipelineRunResponse(**run)


@router.get(
    "/pipeline/runs/{run_id}/decisions",
    response_model=List[RunDecisionResponse],
)
async def get_run_decisions(run_id: int, request: Request):
    state = get_state(request)
    decisions = repo.get_run_decisions(state.db_con, run_id)
    return [RunDecisionResponse(**d) for d in decisions]


@router.get("/pipeline/runs/search", response_model=List[VideoSearchResult])
async def search_video_across_runs(request: Request, video_id: str, limit: int = 50):
    """Search for a video ID across all pipeline runs in a single query."""
    state = get_state(request)
    runs = repo.get_runs_by_video_id(state.db_con, video_id, limit)
    results = []
    for run in runs:
        decisions = repo.get_run_decisions(state.db_con, run["id"], limit=1)
        for d in decisions:
            if d.get("video_id") == video_id:
                results.append(
                    VideoSearchResult(
                        run_id=run["id"],
                        run_started_at=run["started_at"],
                        run_status=run["status"],
                        run_trigger=run["trigger"],
                        run_dry_run=run.get("dry_run", False),
                        pipeline_name=run.get("pipeline_name"),
                        decision=RunDecisionResponse(**d),
                    )
                )
    return results
