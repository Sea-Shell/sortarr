"""sortarr.api.routes.config — application configuration routes."""

import logging

from fastapi import APIRouter, Depends

from sortarr.api.deps import get_state
from sortarr.api.models import ConfigResponse, ConfigUpdate
from sortarr.db.repository import config as config_repo

log = logging.getLogger("sortarr.api.routes.config")

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=ConfigResponse)
async def get_config(state=Depends(get_state)) -> ConfigResponse:
    """Get current configuration.

    Returns:
        Current runtime configuration values.
    """
    return ConfigResponse(
        schedule=state.settings.schedule,
        reprocess_days=state.settings.reprocess_days,
        activity_limit=state.settings.activity_limit,
        subscription_limit=state.settings.subscription_limit,
        published_after=state.settings.published_after,
    )


@router.put("", response_model=ConfigResponse)
async def update_config(
    update: ConfigUpdate, state=Depends(get_state)
) -> ConfigResponse:
    """Update configuration (partial update).

    Persists changes to database and updates scheduler if schedule changed.

    Args:
        update: Configuration fields to update (only non-None fields are updated)

    Returns:
        Updated configuration.
    """
    # Update settings object and persist to database
    if update.schedule is not None:
        state.settings.schedule = update.schedule
        config_repo.set_config("schedule", update.schedule)
        # Update scheduler with new cron expression
        if state.scheduler:
            state.scheduler.update_schedule(update.schedule)
            log.info("scheduler updated with new cron: %s", update.schedule)

    if update.reprocess_days is not None:
        state.settings.reprocess_days = update.reprocess_days
        config_repo.set_config("reprocess_days", str(update.reprocess_days))

    if update.activity_limit is not None:
        state.settings.activity_limit = update.activity_limit
        config_repo.set_config("activity_limit", str(update.activity_limit))

    if update.subscription_limit is not None:
        state.settings.subscription_limit = update.subscription_limit
        config_repo.set_config("subscription_limit", str(update.subscription_limit))

    if update.published_after is not None:
        state.settings.published_after = update.published_after
        config_repo.set_config("published_after", update.published_after)

    log.info("configuration updated")

    return ConfigResponse(
        schedule=state.settings.schedule,
        reprocess_days=state.settings.reprocess_days,
        activity_limit=state.settings.activity_limit,
        subscription_limit=state.settings.subscription_limit,
        published_after=state.settings.published_after,
    )
