"""sortarr.api.app — FastAPI application factory with lifespan."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sortarr.config import load_settings
from sortarr.core.auth import OAuthManager
from sortarr.core.runner import Runner
from sortarr.core.scheduler import PipelineScheduler
from sortarr.core.youtube import YouTubeAPIClient, reset_quota
from sortarr.db.connection import close_db, init_db
from sortarr.db.migrations import init_db as apply_schema

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

log = logging.getLogger("sortarr.api.app")


class AppState:
    """Application state container for dependency injection."""

    def __init__(self) -> None:
        self.settings = load_settings()
        self.oauth_manager: OAuthManager | None = None
        self.youtube_client: YouTubeAPIClient | None = None
        self.runner: Runner | None = None
        self.scheduler: PipelineScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager.

    Startup:
    - Initialize database connection and apply schema
    - Reset quota counter
    - Migrate OAuth credentials from pickle if needed
    - Initialize OAuth manager and YouTube client
    - Create Runner
    - Start scheduler

    Shutdown:
    - Stop scheduler
    - Close database connection
    """
    state: AppState = app.state.sortarr

    # Startup
    log.info("starting sortarr v2 API")

    # 1. Initialize database
    conn = init_db(state.settings.database_file)
    apply_schema(conn, auto_migrate=True)
    log.info("database initialized and schema applied")

    # 2. Reset quota counter on startup
    reset_quota()

    # 3. Initialize OAuth manager
    redirect_uri = f"{state.settings.public_url}/api/auth/callback"
    state.oauth_manager = OAuthManager(
        client_secret_path=state.settings.client_secret_path,
        redirect_uri=redirect_uri,
    )

    # 4. Migrate OAuth credentials from pickle if needed
    migrated = state.oauth_manager.migrate_from_pickle("credentials.pickle")
    if migrated:
        log.warning("OAuth credentials migrated from pickle to database")

    # 5. Initialize YouTube client (only if authenticated)
    if state.oauth_manager.is_authenticated():
        http = state.oauth_manager.get_http()
        state.youtube_client = YouTubeAPIClient(http)
        log.info("YouTube API client initialized")
    else:
        log.warning("YouTube API client NOT initialized — not authenticated")

    # 6. Create Runner (only if YouTube client available)
    if state.youtube_client:
        state.runner = Runner(
            youtube_client=state.youtube_client,
            oauth_manager=state.oauth_manager,
            reprocess_days=state.settings.reprocess_days,
            activity_limit=state.settings.activity_limit,
            subscription_limit=state.settings.subscription_limit,
            published_after=state.settings.published_after,
        )
        log.info("Runner initialized")
    else:
        log.warning("Runner NOT initialized — YouTube client unavailable")

    # 7. Start scheduler
    def scheduled_run_callback() -> None:
        """Callback for scheduled pipeline runs."""
        if state.runner:
            try:
                run_id = state.runner.execute(mode="run")
                log.info("scheduled run completed: run_id=%d", run_id)
            except Exception as e:
                log.error("scheduled run failed: %s", e, exc_info=True)
        else:
            log.warning("scheduled run skipped — Runner not initialized")

    state.scheduler = PipelineScheduler(
        cron_expression=state.settings.schedule,
        run_callback=scheduled_run_callback,
    )
    state.scheduler.start()

    log.info("sortarr v2 API started successfully")

    yield

    # Shutdown
    log.info("shutting down sortarr v2 API")

    if state.scheduler:
        state.scheduler.stop()

    close_db()
    log.info("sortarr v2 API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="sortarr v2",
        description="YouTube playlist automation with pipelines",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Initialize app state
    app.state.sortarr = AppState()

    # CORS middleware (allow all origins for local dev)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from sortarr.api.routes import (
        auth,
        config,
        health,
        metrics,
        pipeline,
        pipelines,
        preview,
        stats,
        subscriptions,
    )

    app.include_router(auth.router, prefix="/api")
    app.include_router(health.router, prefix="/api")
    app.include_router(config.router, prefix="/api")
    app.include_router(pipelines.router, prefix="/api")
    app.include_router(pipeline.router, prefix="/api")
    app.include_router(preview.router, prefix="/api")
    app.include_router(subscriptions.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(metrics.router)  # no /api prefix for Prometheus convention

    # Serve UI static files (must be after API routes)
    # In container: /app/ui/dist (not /app/src/ui/dist)
    ui_dist = Path(__file__).parent.parent.parent.parent / "ui" / "dist"
    if ui_dist.exists():
        # Mount static assets (JS, CSS bundles)
        assets_dir = ui_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            log.info("mounted UI assets from %s", assets_dir)

        # Serve static files at root (favicon, icons)
        @app.get("/favicon.svg")
        async def favicon() -> FileResponse:
            return FileResponse(ui_dist / "favicon.svg")

        @app.get("/icons.svg")
        async def icons() -> FileResponse:
            return FileResponse(ui_dist / "icons.svg")

        # Catch-all route for SPA routing (must be last)
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            """Serve index.html for all non-API routes (SPA routing)."""
            index_file = ui_dist / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            raise HTTPException(status_code=404, detail="Not Found")

        log.info("UI static files configured from %s", ui_dist)
    else:
        log.warning("UI dist directory not found at %s — UI will not be served", ui_dist)

    return app
