import asyncio
import random
import re
import time
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException
from libs.websites import kleinanzeigen as lib
from utils.performance import PageMetrics
from utils.error_handling import (
    WarningManager,
    ErrorLogger,
    ErrorSeverity,
    error_handling_context,
)


def _extract_numeric_ad_id(raw_id: str) -> Optional[str]:
    if not raw_id:
        return None
    if match := re.match(r"(\d+)", raw_id):
        return match[1]
    first_segment = raw_id.split("-", 1)[0]
    digits = re.sub(r"\D", "", first_segment)
    return digits or first_segment or None


async def fetch_listing_views(listing_id: str, client: httpx.AsyncClient) -> Optional[str]:
    ad_id = _extract_numeric_ad_id(listing_id)
    if not ad_id:
        return None
    try:
        response = await client.get(
            "https://www.kleinanzeigen.de/s-vac-inc-get.json",
            params={"adId": ad_id},
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0"
                " Safari/537.36",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        visits = payload.get("numVisits")
        if isinstance(visits, int):
            return str(visits)
        visits_str = payload.get("numVisitsStr")
        if isinstance(visits_str, str):
            clean_value = visits_str.lstrip("0")
            return clean_value or "0"
    except httpx.HTTPError as exc:
        # Views are informational; prefer failing open to avoid breaking the endpoint.
        print(f"[WARN] Unable to fetch views for {listing_id}: {exc}")
    except ValueError as exc:
        print(f"[WARN] Invalid views payload for {listing_id}: {exc}")
    return None


async def get_inserate_details_httpx(
    url: str, client: httpx.AsyncClient, listing_id: str
) -> Dict[str, Any]:
    try:
        response = await client.get(url, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.text, "html.parser")

        # --- Parallel Data Extraction ---
        ad_id = lib.get_element_content(
            soup,
            "#viewad-ad-id-box > ul > li:nth-child(2)",
            default="[ERROR] Ad ID not found",
        )
        categories = [
            cat.strip()
            for cat in lib.get_elements_content(soup, ".breadcrump-link")
            if cat.strip()
        ]
        title = lib.get_element_content(
            soup, "#viewad-title", default="[ERROR] Title not found"
        )
        price_element = lib.get_element_content(soup, "#viewad-price")
        price = lib.parse_price(price_element)
        description = lib.get_element_content(soup, "#viewad-description-text")
        if description:
            description = re.sub(r"[ \t]+", " ", description).strip()
            description = re.sub(r"\n+", "\n", description)

        images = lib.get_image_sources(soup, "#viewad-image")
        seller_details = lib.get_seller_details(soup)
        details = lib.get_details(soup)
        features = lib.get_features(soup)

        shipping_text = lib.get_element_content(
            soup, ".boxedarticle--details--shipping"
        )
        shipping = None
        shipping_cost: Optional[str] = None
        if shipping_text:
            if "Nur Abholung" in shipping_text:
                shipping = "pickup"
            elif "Versand" in shipping_text:
                shipping = "shipping"
                cost_match = re.search(
                    r"Versand\s*(?:ab)?\s*([0-9.,]+)\s*€", shipping_text, re.IGNORECASE
                )
                if cost_match:
                    shipping_cost = f"{cost_match.group(1)} €"
                else:
                    generic_cost = re.search(
                        r"([0-9.,]+)\s*€", shipping_text, re.IGNORECASE
                    )
                    if generic_cost:
                        shipping_cost = f"{generic_cost.group(1)} €"

        location = lib.get_location(soup)
        extra_info = lib.get_extra_info(soup)
        views_api = await fetch_listing_views(ad_id or listing_id, client)
        views_value = views_api or "0"

        # Status is not easily available without JS, so we'll default to active
        status = "active"

        return {
            "id": ad_id,
            "categories": categories,
            "title": title.split(" • ")[-1].strip()
            if " • " in title
            else title.strip(),
            "status": status,
            "price": price,
            "delivery": shipping,
            "delivery_cost": shipping_cost,
            "location": location,
            "views": views_value,
            "description": description,
            "images": images,
            "details": details,
            "features": features,
            "seller": seller_details,
            "extra_info": extra_info,
        }
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] HTTP error for {url}: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Could not fetch ad details from source: {e.response.reason_phrase}",
        ) from e
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_inserate_details_optimized(listing_id: str, retry_count: int = 2) -> Dict[str, Any]:
    from utils.performance import PerformanceTracker

    logger = ErrorLogger("inserat_scraper_httpx")
    warning_manager = WarningManager()
    tracker = PerformanceTracker()
    tracker.start_request()

    url = f"https://www.kleinanzeigen.de/s-anzeige/{listing_id}"

    with error_handling_context(
        operation="fetch_listing_details_httpx",
        listing_id=listing_id,
        url=url,
        logger=logger,
    ) as error_ctx:
        last_structured_error = None

        async with httpx.AsyncClient() as client:
            for attempt in range(retry_count + 1):
                start_time = time.time()
                try:
                    details = await get_inserate_details_httpx(
                        url, client, listing_id
                    )

                    if not details or not details.get("id"):
                        warning_manager.add_warning(
                            f"Incomplete data extracted for listing {listing_id}",
                            ErrorSeverity.MEDIUM,
                            error_ctx.context,
                            affected_items=[listing_id],
                            impact_description="Some listing information may be missing",
                        )

                    page_metric = PageMetrics(
                        page_number=1,
                        url=url,
                        start_time=start_time,
                        end_time=time.time(),
                        success=True,
                        retry_count=attempt,
                        error_message=None,
                        results_count=1,
                        warning_count=len(warning_manager.get_warnings()),
                    )
                    tracker.add_page_metric(page_metric)

                    request_metrics = tracker.get_request_metrics()

                    response = {
                        "success": True,
                        "data": details,
                        "time_taken": round(request_metrics.total_time, 3),
                        "performance_metrics": request_metrics.to_dict(),
                    }

                    if warnings := warning_manager.get_warnings():
                        response["warnings"] = (
                            warning_manager.get_user_friendly_messages()
                        )
                        response["detailed_warnings"] = [w.to_dict() for w in warnings]
                        response["warning_summary"] = (
                            warning_manager.get_warning_summary()
                        )

                    return response

                except Exception as e:
                    error_ctx.context.retry_attempt = attempt
                    structured_error = error_ctx.handle_exception(
                        e, "detail_fetch_httpx"
                    )
                    last_structured_error = structured_error

                    if attempt < retry_count and structured_error.should_retry(
                        retry_count
                    ):
                        warning_manager.add_warning(
                            f"Retrying listing {listing_id} after {structured_error.category.value} error (attempt {attempt + 1}/{retry_count + 1})",
                            ErrorSeverity.MEDIUM,
                            error_ctx.context,
                            affected_items=[listing_id],
                            impact_description=f"Temporary delay before retry due to {structured_error.category.value} error",
                        )
                        wait_time = (2**attempt) + random.uniform(0, 1)
                        await asyncio.sleep(wait_time)
                        continue

                    error_msg = f"Failed after {attempt + 1} attempts: {structured_error.message}"
                    page_metric = PageMetrics(
                        page_number=1,
                        url=url,
                        start_time=start_time,
                        end_time=time.time(),
                        success=False,
                        retry_count=attempt,
                        error_message=error_msg,
                        results_count=0,
                        error_category=structured_error.category.value,
                        warning_count=len(warning_manager.get_warnings()),
                    )
                    tracker.add_page_metric(page_metric)

                    request_metrics = tracker.get_request_metrics()

                    response = {
                        "success": False,
                        "error": structured_error.message,
                        "error_category": structured_error.category.value,
                        "error_severity": structured_error.severity.value,
                        "recovery_suggestions": structured_error.recovery_suggestions,
                        "data": None,
                        "time_taken": round(request_metrics.total_time, 3),
                        "performance_metrics": request_metrics.to_dict(),
                    }

                    if warnings := warning_manager.get_warnings():
                        response["warnings"] = (
                            warning_manager.get_user_friendly_messages()
                        )
                        response["detailed_warnings"] = [w.to_dict() for w in warnings]

                    return response

        if last_structured_error:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": last_structured_error.message,
                    "category": last_structured_error.category.value,
                    "severity": last_structured_error.severity.value,
                    "recovery_suggestions": last_structured_error.recovery_suggestions,
                },
            )
        else:
            raise HTTPException(
                status_code=500, detail="Unexpected error in retry loop"
            )
