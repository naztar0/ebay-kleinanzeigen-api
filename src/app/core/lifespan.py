from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from loguru import logger

from ..services.http_client import create_shared_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: shared HTTP client and in-memory cache."""
    if sys.platform != "win32":
        try:
            import uvloop

            uvloop.install()
        except ImportError:
            logger.warning("uvloop not available; using default asyncio event loop")

    app.state.http_client = create_shared_client()
    FastAPICache.init(InMemoryBackend())
    logger.info("Application startup complete")
    yield
    await app.state.http_client.aclose()
    logger.info("Application shutdown complete")
