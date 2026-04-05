"""Listing detail endpoint."""

from __future__ import annotations

import re
import time

import httpx
from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from loguru import logger

from ...api.dependencies import ScraperDep
from ...exceptions import KleinanzeigenBannedError
from ...models import ApiResponse, ListingDetail

router = APIRouter(prefix="/v1", tags=["Listing Details"])

_LISTING_ID_RE = re.compile(r"^\d{5,15}(-[a-z0-9-]+)?$")


@router.get("/listings/{listing_id}", response_model=ApiResponse[ListingDetail])
@cache(expire=300)
async def get_listing_detail(
    listing_id: str, scraper: ScraperDep
) -> ApiResponse[ListingDetail]:
    if not _LISTING_ID_RE.match(listing_id):
        raise HTTPException(status_code=400, detail="Invalid listing ID format")

    started_at = time.perf_counter()
    try:
        detail = await scraper.fetch_listing_detail(listing_id)
    except KleinanzeigenBannedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.is_redirect or exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Listing not found") from exc
        logger.warning(
            "HTTP error %d fetching listing %s", exc.response.status_code, listing_id
        )
        raise HTTPException(status_code=502, detail="Failed to fetch listing") from exc
    except httpx.HTTPError as exc:
        logger.exception("Network error fetching listing %s: %s", listing_id, exc)
        raise HTTPException(status_code=502, detail="Failed to fetch listing") from exc

    elapsed = round(time.perf_counter() - started_at, 3)
    return ApiResponse(success=True, data=detail, time_taken=elapsed)
