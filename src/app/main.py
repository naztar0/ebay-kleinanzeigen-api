from __future__ import annotations

from fastapi import FastAPI

from .api.routes import listing_details, listings, listings_detailed
from .core.config import get_settings
from .core.logging import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    setup_logging(
        console_level=settings.logging_console_level,
        file_level=settings.logging_file_level,
        app_name=settings.logging_app_name,
    )

    app = FastAPI(
        title="Kleinanzeigen API",
        version=settings.api_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
    )

    app.include_router(listings.router)
    app.include_router(listing_details.router)
    app.include_router(listings_detailed.router)

    return app


app = create_app()
