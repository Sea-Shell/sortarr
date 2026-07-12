import logging

from pydantic_settings import BaseSettings

log = logging.getLogger("sortarr.config")


class Settings(BaseSettings):
    """sortarr v2 settings — loaded from SORTARR_* env vars and .env file."""

    model_config = {
        "env_prefix": "SORTARR_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    # Schedule
    schedule: str = "0 */6 * * *"  # cron expression for pipeline runs
    reprocess_days: int = 2  # days back for title_similarity comparison

    # Limits
    activity_limit: int = 0  # max activities per subscription per fetch (0=unlimited)
    subscription_limit: int = 0  # max subscriptions to fetch (0=unlimited)
    published_after: str | None = None  # ISO 8601, overrides watermark

    # General
    public_url: str = "http://localhost:8080"  # public-facing URL for OAuth callback
    client_secret_path: str = "client_secret.json"  # path to Google OAuth client secret
    database_file: str = "sortarr.db"
    log_level: str = "warning"

    # Legacy fields kept for compatibility
    api_port: int = 8080


def load_settings() -> Settings:
    s = Settings()
    log.debug("config loaded: %s", s.model_dump())
    return s
