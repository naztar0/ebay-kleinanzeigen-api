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


class ListingsResponse(BaseModel):
    success: bool = True
    results: List[ListingSummary] = Field(default_factory=list)
    total_results: int = Field(..., ge=0)
    time_taken: float = Field(..., ge=0)
