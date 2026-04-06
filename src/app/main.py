from __future__ import annotations

import contextlib
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .api.routes import health, listing_details, listings, listings_detailed
from .core.config import get_settings
from .core.lifespan import lifespan
from .core.logging import setup_logging
from .exceptions import KleinanzeigenBannedError
from .middleware.request_id import RequestIDMiddleware
from .models.responses import ApiErrorResponse

if sys.platform != "win32":
    with contextlib.suppress(ImportError):
        import uvloop

        uvloop.install()


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
        lifespan=lifespan,
    )

    # Rate limiter (must be set up before SlowAPIMiddleware is added)
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[
            f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds}second"
        ],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    if settings.rate_limit_enabled:
        app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(KleinanzeigenBannedError)
    async def banned_exc_handler(
        request: Request, exc: KleinanzeigenBannedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=ApiErrorResponse(
                error=str(exc), error_category="ip_banned"
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiErrorResponse(error=str(exc.detail)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exc_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s: %s", request.url, exc)
        return JSONResponse(
            status_code=500,
            content=ApiErrorResponse(
                error="Internal server error", error_category="unhandled"
            ).model_dump(),
        )

    app.include_router(health.router)
    app.include_router(listings.router)
    app.include_router(listing_details.router)
    app.include_router(listings_detailed.router)

    return app


app = create_app()
