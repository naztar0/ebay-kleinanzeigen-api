from __future__ import annotations

from typing import Any, Dict

import httpx
from loguru import logger

from ..core.config import get_settings


class HttpClientFactory:
    """Factory for configured HTTPX async clients."""

    @staticmethod
    def create_async_client() -> httpx.AsyncClient:
        settings = get_settings()
        timeout = httpx.Timeout(settings.http_timeout)
        transport = httpx.AsyncHTTPTransport(retries=settings.http_max_retries)
        return httpx.AsyncClient(timeout=timeout, transport=transport)


async def fetch_json(
    client: httpx.AsyncClient, url: str, *, params: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Fetch JSON content from the given URL with error handling."""

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"HTTP error {exc.response.status_code} for {exc.request.url}")
        raise
    except httpx.HTTPError as exc:
        logger.error(f"HTTP client error for {url}: {exc}")
        raise
