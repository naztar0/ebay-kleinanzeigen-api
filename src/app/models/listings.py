from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Price(BaseModel):
    amount: float = Field(..., ge=0)
    currency: str = Field(..., min_length=1)
    negotiable: bool = Field(default=False)


class Location(BaseModel):
    zip: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: Optional[str] = None


class Seller(BaseModel):
    name: Optional[str] = None
    since: Optional[str] = None
    type: str = Field(default="private")
    badges: List[str] = Field(default_factory=list)


class ListingDetail(BaseModel):
    id: str = Field(..., min_length=1)
    categories: List[str] = Field(default_factory=list)
    title: str = Field(..., min_length=1)
    status: str = Field(default="active")
    price: Price
    delivery: Optional[str] = None
    delivery_cost: Optional[str] = None
    location: Location
    views: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    details: Dict[str, str] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    seller: Seller
    extra_info: Dict[str, Optional[str]] = Field(default_factory=dict)


class ListingSummary(BaseModel):
    ad_id: str = Field(..., alias="adid")
    url: str
    title: str
    price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    negotiable: bool = Field(default=False)
    description_snippet: Optional[str] = Field(default=None, alias="description")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }

    @field_validator("price", mode="before")
    @classmethod
    def _coerce_price(cls, value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class PaginationMetadata(BaseModel):
    """Metadata about pagination and search results."""

    pages_requested: int = Field(..., ge=1, description="Number of pages requested")
    pages_fetched: int = Field(
        ..., ge=0, description="Number of pages actually fetched"
    )
    start_page: int = Field(default=1, ge=1, description="Starting page number")
    end_page: int = Field(..., ge=1, description="Ending page number")
    total_available_results: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total results available from search (if detected)",
    )
    results_per_page: int = Field(default=25, ge=1, description="Results per page")
    duplicates_removed: int = Field(
        default=0, ge=0, description="Number of duplicate listings removed"
    )


class ListingsResponse(BaseModel):
    success: bool = True
    results: List[ListingSummary] = Field(default_factory=list)
    total_results: int = Field(..., ge=0)
    pagination: Optional[PaginationMetadata] = None
    time_taken: float = Field(..., ge=0)
