from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    api_version: str = Field(default="2.0.0", description="API version string")
    docs_url: str | None = Field(
        default="/docs", description="OpenAPI documentation path"
    )
    redoc_url: str | None = Field(
        default="/redoc", description="ReDoc documentation path"
    )

    # HTTP client
    http_timeout: float = Field(
        default=15.0, gt=0, description="Default HTTP client timeout (seconds)"
    )
    http_max_retries: int = Field(
        default=3, ge=0, le=10, description="Default HTTP retry count"
    )
    http_user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        description="Default User-Agent header for HTTP scraping",
    )
    http_max_connections: int = Field(
        default=50, ge=1, description="Max total HTTP connections in the shared pool"
    )
    http_max_keepalive_connections: int = Field(
        default=20,
        ge=1,
        description="Max keepalive HTTP connections in the shared pool",
    )

    # Scraping
    page_fetch_concurrency: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max concurrent page fetches when scraping multiple pages",
    )

    # Logging
    logging_console_level: str = Field(
        default="INFO", description="Console log level for Loguru sinks"
    )
    logging_file_level: str = Field(
        default="DEBUG", description="File log level for Loguru sinks"
    )
    logging_app_name: str = Field(
        default="kleinanzeigen-api",
        description="Application name used for log files",
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=False, description="Enable global rate limiting middleware"
    )
    rate_limit_requests: int = Field(
        default=60, description="Requests per window when rate limiting"
    )
    rate_limit_window_seconds: int = Field(
        default=60, description="Rate limit window size in seconds"
    )

    # CORS
    cors_allow_origins: list[str] = Field(
        default=["*"], description="Allowed CORS origins"
    )

    # Caching
    cache_ttl_seconds: int = Field(
        default=60, ge=0, description="Cache TTL in seconds for listing responses"
    )
    cache_ttl_detail_seconds: int = Field(
        default=300,
        ge=0,
        description="Cache TTL in seconds for single-listing detail responses",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
