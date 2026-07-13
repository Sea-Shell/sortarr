"""sortarr.api.routes.pipelines — Pipeline CRUD routes."""

import logging

from fastapi import APIRouter, HTTPException, Response

from sortarr.api.models import ReorderRequest, SetJunctionRequest
from sortarr.db.repository.pipelines import (
    create_pipeline,
    delete_pipeline,
    get_pipeline,
    list_pipelines,
    reorder_pipelines,
    set_ignore_lists,
    set_selectors,
    set_subscriptions,
    update_pipeline,
)
from sortarr.models.pipeline import (
    PipelineCreate,
    PipelineResponse,
    PipelineUpdate,
)

log = logging.getLogger("sortarr.api.routes.pipelines")

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("", response_model=list[PipelineResponse])
async def get_pipelines():
    """List all pipelines with junction table data.

    Returns pipelines ordered by sort_order, then name.
    """
    try:
        return list_pipelines()
    except Exception as e:
        log.error("failed to list pipelines: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to list pipelines: {e}") from e


@router.post("", response_model=PipelineResponse, status_code=201)
async def create_pipeline_route(pipeline: PipelineCreate):
    """Create a new pipeline.

    Accepts junction table IDs (ignore_list_ids, selector_ids, subscription_ids)
    in the request body and sets them atomically with the pipeline creation.

    Returns 201 with the created pipeline.
    """
    try:
        created = create_pipeline(pipeline)
        # Fetch junction table data to match PipelineResponse schema
        from sortarr.db.repository.pipelines import (
            get_pipeline_ignore_lists,
            get_pipeline_selectors,
            get_pipeline_subscriptions,
        )

        return PipelineResponse(
            id=created.id,
            name=created.name,
            enabled=created.enabled,
            order=created.order,
            playlist_id=created.playlist_id,
            subscription_scope=created.subscription_scope,
            duration_min_seconds=created.duration_min_seconds,
            duration_max_seconds=created.duration_max_seconds,
            selector_mode=created.selector_mode,
            ignore_list_ids=get_pipeline_ignore_lists(created.id),
            selector_ids=get_pipeline_selectors(created.id),
            subscription_ids=get_pipeline_subscriptions(created.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except Exception as e:
        log.error("failed to create pipeline: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to create pipeline: {e}") from e


@router.put("/reorder", status_code=204)
async def reorder_pipelines_route(request: ReorderRequest):
    """Reorder pipelines by setting sort_order.

    Accepts a list of pipeline IDs in the desired order.
    Returns 204 No Content on success.
    """
    try:
        reorder_pipelines(request.pipeline_ids)
        return Response(status_code=204)
    except Exception as e:
        log.error("failed to reorder pipelines: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to reorder pipelines: {e}") from e


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline_by_id(pipeline_id: str):
    """Get a single pipeline by ID.

    Returns 404 if pipeline not found.
    """
    try:
        pipeline = get_pipeline(pipeline_id)
        # Fetch junction table data to match PipelineResponse schema
        from sortarr.db.repository.pipelines import (
            get_pipeline_ignore_lists,
            get_pipeline_selectors,
            get_pipeline_subscriptions,
        )

        return PipelineResponse(
            id=pipeline.id,
            name=pipeline.name,
            enabled=pipeline.enabled,
            order=pipeline.order,
            playlist_id=pipeline.playlist_id,
            subscription_scope=pipeline.subscription_scope,
            duration_min_seconds=pipeline.duration_min_seconds,
            duration_max_seconds=pipeline.duration_max_seconds,
            selector_mode=pipeline.selector_mode,
            ignore_list_ids=get_pipeline_ignore_lists(pipeline_id),
            selector_ids=get_pipeline_selectors(pipeline_id),
            subscription_ids=get_pipeline_subscriptions(pipeline_id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        log.error("failed to get pipeline %s: %s", pipeline_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to get pipeline: {e}") from e


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline_route(pipeline_id: str, updates: PipelineUpdate):
    """Update a pipeline (partial update).

    Only non-None fields in the request body are updated.
    Returns 404 if pipeline not found.
    """
    try:
        updated = update_pipeline(pipeline_id, updates)
        # Fetch junction table data to match PipelineResponse schema
        from sortarr.db.repository.pipelines import (
            get_pipeline_ignore_lists,
            get_pipeline_selectors,
            get_pipeline_subscriptions,
        )

        return PipelineResponse(
            id=updated.id,
            name=updated.name,
            enabled=updated.enabled,
            order=updated.order,
            playlist_id=updated.playlist_id,
            subscription_scope=updated.subscription_scope,
            duration_min_seconds=updated.duration_min_seconds,
            duration_max_seconds=updated.duration_max_seconds,
            selector_mode=updated.selector_mode,
            ignore_list_ids=get_pipeline_ignore_lists(updated.id),
            selector_ids=get_pipeline_selectors(updated.id),
            subscription_ids=get_pipeline_subscriptions(updated.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        log.error("failed to update pipeline %s: %s", pipeline_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to update pipeline: {e}") from e


@router.delete("/{pipeline_id}", status_code=204)
async def delete_pipeline_route(pipeline_id: str):
    """Delete a pipeline.

    Cascade deletes junction table entries via foreign key constraints.
    Returns 204 No Content on success.
    """
    try:
        delete_pipeline(pipeline_id)
        return Response(status_code=204)
    except Exception as e:
        log.error("failed to delete pipeline %s: %s", pipeline_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to delete pipeline: {e}") from e


@router.put("/{pipeline_id}/ignore-lists", status_code=204)
async def set_pipeline_ignore_lists(pipeline_id: str, request: SetJunctionRequest):
    """Set ignore lists for a pipeline.

    Replaces all existing associations with the provided list.
    Returns 204 No Content on success.
    """
    try:
        set_ignore_lists(pipeline_id, request.ids)
        return Response(status_code=204)
    except Exception as e:
        log.error("failed to set ignore lists for pipeline %s: %s", pipeline_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to set ignore lists: {e}") from e


@router.put("/{pipeline_id}/selectors", status_code=204)
async def set_pipeline_selectors(pipeline_id: str, request: SetJunctionRequest):
    """Set selectors for a pipeline.

    Replaces all existing associations with the provided list.
    Returns 204 No Content on success.
    Returns 501 if trying to add selectors (not yet implemented).
    """
    try:
        set_selectors(pipeline_id, request.ids)
        return Response(status_code=204)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except Exception as e:
        log.error("failed to set selectors for pipeline %s: %s", pipeline_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to set selectors: {e}") from e


@router.put("/{pipeline_id}/subscriptions", status_code=204)
async def set_pipeline_subscriptions(pipeline_id: str, request: SetJunctionRequest):
    """Set subscriptions for a pipeline.

    Replaces all existing associations with the provided list.
    Returns 204 No Content on success.
    """
    try:
        set_subscriptions(pipeline_id, request.ids)
        return Response(status_code=204)
    except Exception as e:
        log.error("failed to set subscriptions for pipeline %s: %s", pipeline_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"failed to set subscriptions: {e}") from e

