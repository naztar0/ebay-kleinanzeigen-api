"""Listings search endpoint."""

from __future__ import annotations

import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi_cache.decorator import cache

from ...api.dependencies import ScraperDep
from ...exceptions import KleinanzeigenBannedError
from ...models import ApiResponse, ListingsResponse

router = APIRouter(prefix="/v1", tags=["Listings"])


@router.get("/listings", response_model=ApiResponse[ListingsResponse])
@cache(expire=60)
async def search_listings(
    scraper: ScraperDep,
    query: str | None = Query(None, description="Search term"),
    location: str | None = Query(None, description="Location filter"),
    radius: int | None = Query(None, ge=1, le=100, description="Radius in km"),
    min_price: int | None = Query(None, ge=0, description="Minimum price filter"),
    max_price: int | None = Query(None, ge=0, description="Maximum price filter"),
    sort_by: Literal["lowest", "price", "preis", "highest", "teuerste"] | None = Query(
        None,
        description=(
            "Sort order: 'lowest'/'price'/'preis' (cheapest first), "
            "'highest'/'teuerste' (most expensive first), or omit for newest first"
        ),
    ),
    page_count: int = Query(1, ge=1, le=10, description="Number of pages to fetch"),
    start_page: int = Query(
        1, ge=1, le=200, description="Starting page number (default: 1)"
    ),
) -> ApiResponse[ListingsResponse]:
    started_at = time.perf_counter()
    try:
        listings, metrics, pagination = await scraper.fetch_listings(
            query=query,
            location=location,
            radius=radius,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            page_count=page_count,
            start_page=start_page,
        )
    except KleinanzeigenBannedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    elapsed = round(time.perf_counter() - started_at, 3)
    payload = ListingsResponse(
        results=listings,
        total_results=len(listings),
        pagination=pagination,
        metrics=metrics,
        time_taken=elapsed,
    )
    return ApiResponse(success=True, data=payload, time_taken=elapsed)
