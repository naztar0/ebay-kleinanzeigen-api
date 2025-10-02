from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PageMetric(BaseModel):
    page_number: int = Field(..., ge=1)
    time_taken: float = Field(..., ge=0)
    success: bool
    retry_count: int = Field(..., ge=0)
    results_count: int = Field(..., ge=0)
    duplicates_found: int = Field(default=0, ge=0)
    error: Optional[str] = None
    error_category: Optional[str] = None
    warning_count: Optional[int] = Field(None, ge=0)


class PerformanceMetrics(BaseModel):
    pages_requested: int = Field(..., ge=0)
    pages_successful: int = Field(..., ge=0)
    pages_failed: int = Field(..., ge=0)
    concurrency: Optional[int] = Field(None, ge=0)
    success_rate: float = Field(..., ge=0, le=100)
    average_page_time: float = Field(..., ge=0)
    fastest_page_time: float = Field(..., ge=0)
    slowest_page_time: float = Field(..., ge=0)
    page_details: List[PageMetric] = Field(default_factory=list)
