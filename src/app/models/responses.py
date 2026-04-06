from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    time_taken: Optional[float] = Field(None, ge=0)


class ApiErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_category: Optional[str] = None
    error_severity: Optional[str] = None
    recovery_suggestions: Optional[list[str]] = None
    time_taken: Optional[float] = Field(None, ge=0)
