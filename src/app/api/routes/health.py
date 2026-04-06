from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Meta"])


@router.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    """Health check for load balancers, Docker, and uptime monitors."""
    return {"status": "ok"}
