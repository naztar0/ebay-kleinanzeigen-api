"""Listing detail endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from loguru import logger

from ...models import ApiResponse, ListingDetail
from ...services import KleinanzeigenScraperService

router = APIRouter(prefix="/v1", tags=["Listing Details"])


@router.get("/listings/{listing_id}", response_model=ApiResponse[ListingDetail])
async def get_listing_detail(listing_id: str) -> ApiResponse[ListingDetail]:
    if not listing_id or not listing_id.strip():
        raise HTTPException(status_code=400, detail="Invalid listing ID")

    started_at = time.perf_counter()
    service = KleinanzeigenScraperService()
    try:
        detail = await service.fetch_listing_detail(listing_id)
        elapsed = round(time.perf_counter() - started_at, 3)
        return ApiResponse(success=True, data=detail, time_taken=elapsed)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to fetch listing detail: {exc}")
        raise HTTPException(
            status_code=502, detail="Failed to fetch listing detail"
        ) from exc
    finally:
        await service.close()
