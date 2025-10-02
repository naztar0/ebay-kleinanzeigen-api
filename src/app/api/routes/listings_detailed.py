"""Listings with details endpoint."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from ...models import ApiResponse
from ...services import KleinanzeigenScraperService

router = APIRouter(prefix="/v1", tags=["Listings"])


@router.get("/listings-detailed", response_model=ApiResponse[list])
async def search_listings_with_details(
    query: Optional[str] = Query(None, description="Search term"),
    location: Optional[str] = Query(None, description="Location filter"),
    radius: Optional[int] = Query(None, ge=1, le=100, description="Radius in km"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price filter"),
    sort_by: Optional[str] = Query(
        None,
        description="Sort order: 'price'/'lowest'/'preis' (lowest first), 'highest'/'teuerste' (highest first), or None (newest first)",
    ),
    page_count: int = Query(1, ge=1, le=5, description="Number of pages to fetch"),
    start_page: int = Query(1, ge=1, description="Starting page number (default: 1)"),
    max_concurrent_details: int = Query(
        10, ge=1, le=20, description="Max concurrent detail fetches"
    ),
) -> ApiResponse[list]:
    started_at = time.perf_counter()
    service = KleinanzeigenScraperService()
    try:
        combined = await service.fetch_listings_with_details(
            query=query,
            location=location,
            radius=radius,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            page_count=page_count,
            start_page=start_page,
            max_concurrent_details=max_concurrent_details,
        )
        elapsed = round(time.perf_counter() - started_at, 3)
        formatted = [
            {
                "summary": item["summary"],
                "detail": item["detail"],
            }
            for item in combined
        ]
        return ApiResponse(success=True, data=formatted, time_taken=elapsed)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to fetch listings with details: {exc}")
        raise HTTPException(status_code=502, detail="Failed to fetch listings") from exc
    finally:
        await service.close()
