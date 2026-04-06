from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import Depends, Request

from ..services.scraper import KleinanzeigenScraperService


def get_scraper(request: Request) -> KleinanzeigenScraperService:
    """Provide a scraper backed by the application-scoped shared HTTP client."""
    client: httpx.AsyncClient = request.app.state.http_client
    return KleinanzeigenScraperService(client=client)


ScraperDep = Annotated[KleinanzeigenScraperService, Depends(get_scraper)]
