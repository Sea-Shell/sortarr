"""sortarr v2 — entry point."""

from __future__ import annotations

import argparse
import logging
import signal
import sys

import uvicorn

from sortarr.api.app import create_app
from sortarr.config import load_settings

log = logging.getLogger("sortarr")


def setup_logging(level: str) -> None:
    """Configure structured logging."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def handle_shutdown(signum: int, frame) -> None:
    """Handle SIGTERM for graceful shutdown."""
    log.info("received signal %d, shutting down gracefully", signum)
    sys.exit(0)


def main() -> None:
    """Main entry point for sortarr v2."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="sortarr v2 - YouTube playlist automation"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the server to (default: from SORTARR_API_PORT or 8080)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Log level (default: from SORTARR_LOG_LEVEL or warning)",
    )
    args = parser.parse_args()

    # Load settings from environment
    settings = load_settings()

    # Determine port and log level
    port = args.port if args.port is not None else settings.api_port
    log_level = args.log_level if args.log_level is not None else settings.log_level

    # Setup logging
    setup_logging(log_level)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Log startup info
    log.info("starting sortarr v2.0.0")
    log.info("server will listen on %s:%d", args.host, port)
    log.info("public URL: %s", settings.public_url)
    log.info("database: %s", settings.database_file)
    log.info("schedule: %s", settings.schedule)

    # Create FastAPI app
    app = create_app()

    # Start uvicorn server
    uvicorn.run(
        app,
        host=args.host,
        port=port,
        log_level=log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()
