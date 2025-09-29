from __future__ import annotations

from functools import lru_cache
from typing import Optional

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

    api_version: str = Field(default="1.0.0", description="API version string")
    docs_url: Optional[str] = Field(
        default="/docs", description="OpenAPI documentation path"
    )
    redoc_url: Optional[str] = Field(
        default="/redoc", description="ReDoc documentation path"
    )

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

    rate_limit_enabled: bool = Field(
        default=False, description="Enable global rate limiting middleware"
    )
    rate_limit_requests: int = Field(
        default=60, description="Requests per window when rate limiting"
    )
    rate_limit_window_seconds: int = Field(
        default=60, description="Rate limit window size in seconds"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
