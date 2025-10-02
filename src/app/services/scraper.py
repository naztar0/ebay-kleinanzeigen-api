from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger

from ..core.config import get_settings
from ..models.listings import ListingDetail, ListingSummary, PaginationMetadata
from ..models.metrics import PageMetric, PerformanceMetrics
from .http_client import HttpClientFactory, fetch_json
from .parsers.detail_parser import (
    parse_categories,
    parse_details,
    parse_extra_info,
    parse_images,
    parse_location,
    parse_price,
    parse_seller,
)


class KleinanzeigenScraperService:
    """Service for scraping Kleinanzeigen listings via HTTP requests."""

    BASE_URL = "https://www.kleinanzeigen.de"
    LISTINGS_SEARCH_PATH = "/s-suche/k0"
    LISTING_DETAILS_URL = "https://www.kleinanzeigen.de/s-anzeige/{listing_id}"
    LISTING_VIEWS_URL = "https://www.kleinanzeigen.de/s-vac-inc-get.json"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = HttpClientFactory.create_async_client()

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_listing_views(self, listing_id: str) -> int | None:
        normalized_id = self._normalize_listing_id(listing_id)
        params = {"adId": normalized_id}
        try:
            data = await fetch_json(self._client, self.LISTING_VIEWS_URL, params=params)
        except httpx.HTTPError:
            return None

        visits = data.get("numVisits")
        if isinstance(visits, int):
            return visits
        visits_str = data.get("numVisitsStr")
        if isinstance(visits_str, str):
            stripped = visits_str.lstrip("0")
            return int(stripped) if stripped.isdigit() else None
        return None

    @staticmethod
    def _normalize_listing_id(listing_id: str) -> str:
        digits_only = "".join(ch for ch in listing_id if ch.isdigit())
        return digits_only or listing_id.split("-", 1)[0]

    async def fetch_listing_detail(self, listing_id: str) -> ListingDetail:
        url = self.LISTING_DETAILS_URL.format(listing_id=listing_id)
        logger.debug(f"Fetching listing detail from {url}")

        headers = {"User-Agent": self._settings.http_user_agent}
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        raw_price = soup.select_one("#viewad-price")
        price_data = parse_price(raw_price.get_text() if raw_price else None)

        title_element = soup.select_one("#viewad-title")
        title = title_element.get_text(strip=True) if title_element else ""

        views = await self.fetch_listing_views(listing_id)

        return ListingDetail.model_validate(
            {
                "id": listing_id,
                "categories": parse_categories(soup),
                "title": title,
                "status": "active",
                "price": price_data,
                "delivery": self._parse_delivery_method(soup),
                "delivery_cost": self._parse_delivery_cost(soup),
                "location": parse_location(soup),
                "views": views,
                "description": self._extract_description(soup),
                "images": parse_images(soup),
                "details": parse_details(soup),
                "features": self._extract_features(soup),
                "seller": parse_seller(soup),
                "extra_info": parse_extra_info(soup),
            }
        )

    async def fetch_listings(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        radius: int | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        sort_by: str | None = None,
        page_count: int = 1,
        start_page: int = 1,
    ) -> tuple[list[ListingSummary], PerformanceMetrics, PaginationMetadata]:
        page_metrics: List[PageMetric] = []
        summaries: List[ListingSummary] = []
        seen_ad_ids: set[str] = set()
        duplicates_removed = 0
        total_available_results: int | None = None

        end_page = start_page + page_count - 1
        last_page_reached = False

        for page_number in range(start_page, end_page + 1):
            # Stop if we already know there are no more pages
            if last_page_reached:
                logger.debug(
                    f"Skipping page {page_number} - last available page already reached"
                )
                break

            page_metric, page_total_results = await self._fetch_listings_page(
                page_number=page_number,
                query=query,
                location=location,
                radius=radius,
                min_price=min_price,
                max_price=max_price,
                sort_by=sort_by,
                summaries=summaries,
                seen_ad_ids=seen_ad_ids,
            )
            page_metrics.append(page_metric)

            # Store total results from first successful page
            if page_total_results is not None and total_available_results is None:
                total_available_results = page_total_results

            # Count duplicates
            if page_metric.duplicates_found:
                duplicates_removed += page_metric.duplicates_found

            # Check if we hit a redirect (302) - means no more pages available
            # The error message will contain "Redirect response '302"
            if (
                not page_metric.success
                and page_metric.error
                and "302" in page_metric.error
            ):
                last_page_reached = True
                logger.info(
                    f"Reached last available page at page {page_number - 1}. "
                    f"Stopping pagination early."
                )

        metrics = PerformanceMetrics(
            pages_requested=page_count,
            pages_successful=sum(bool(metric.success) for metric in page_metrics),
            pages_failed=sum(not metric.success for metric in page_metrics),
            concurrency=1,
            success_rate=(
                100.0
                if page_count == 0
                else (sum(bool(metric.success) for metric in page_metrics) / page_count)
                * 100
            ),
            average_page_time=(
                sum(metric.time_taken for metric in page_metrics) / page_count
                if page_metrics
                else 0.0
            ),
            fastest_page_time=min(
                (metric.time_taken for metric in page_metrics), default=0.0
            ),
            slowest_page_time=max(
                (metric.time_taken for metric in page_metrics), default=0.0
            ),
            page_details=page_metrics,
        )

        pagination_metadata = PaginationMetadata(
            pages_requested=page_count,
            pages_fetched=len([m for m in page_metrics if m.success]),
            start_page=start_page,
            end_page=end_page,
            total_available_results=total_available_results,
            results_per_page=25,
            duplicates_removed=duplicates_removed,
        )

        return summaries, metrics, pagination_metadata

    @staticmethod
    def _matches_price_filters(
        summary: ListingSummary,
        min_price: int | None,
        max_price: int | None,
    ) -> bool:
        price = summary.price
        if price is None:
            return min_price is None and max_price is None
        if min_price is not None and price < min_price:
            return False
        return max_price is None or price <= max_price

    async def fetch_listings_with_details(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        radius: int | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        sort_by: str | None = None,
        page_count: int = 1,
        start_page: int = 1,
        max_concurrent_details: int = 10,
    ) -> List[Dict[str, Any]]:
        listings, _, _ = await self.fetch_listings(
            query=query,
            location=location,
            radius=radius,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            page_count=page_count,
            start_page=start_page,
        )

        semaphore = asyncio.Semaphore(max_concurrent_details)

        async def fetch_detail(summary: ListingSummary) -> Dict[str, Any] | None:
            async with semaphore:
                try:
                    detail = await self.fetch_listing_detail(summary.ad_id)
                except httpx.HTTPError as exc:
                    logger.warning(f"Failed to fetch detail for {summary.ad_id}: {exc}")
                    return None

                return {
                    "summary": summary,
                    "detail": detail,
                }

        tasks = [fetch_detail(summary) for summary in listings]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, dict):
                combined.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Detail fetch task failed: {result}")

        return combined

    async def _fetch_listings_page(
        self,
        *,
        page_number: int,
        query: str | None,
        location: str | None,
        radius: int | None,
        min_price: int | None,
        max_price: int | None,
        sort_by: str | None,
        summaries: List[ListingSummary],
        seen_ad_ids: set[str],
    ) -> tuple[PageMetric, int | None]:
        import time

        start_time = time.perf_counter()
        try:
            url = self._build_search_url(
                page_number=page_number,
                query=query,
                location=location,
                radius=radius,
                min_price=min_price,
                max_price=max_price,
                sort_by=sort_by,
            )
            logger.debug(f"Fetching listing page {page_number} via {url}")
            headers = {"User-Agent": self._settings.http_user_agent}
            response = await self._client.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract total available results from breadcrumb
            total_results = self._extract_total_results(soup)

            articles = soup.select("article.aditem[data-adid]")
            count = 0
            duplicates_found = 0

            for article in articles:
                if summary := self._parse_listing_summary(article):
                    # Check for duplicates
                    if summary.ad_id in seen_ad_ids:
                        duplicates_found += 1
                        logger.debug(f"Duplicate ad_id found: {summary.ad_id}")
                        continue

                    seen_ad_ids.add(summary.ad_id)
                    summaries.append(summary)
                    count += 1

            duration = time.perf_counter() - start_time
            metric = PageMetric(
                page_number=page_number,
                time_taken=duration,
                success=True,
                retry_count=0,
                results_count=count,
                duplicates_found=duplicates_found,
            )

            return metric, total_results
        except httpx.HTTPError as exc:
            duration = time.perf_counter() - start_time
            logger.warning(f"Failed to fetch page {page_number}: {exc}")
            metric = PageMetric(
                page_number=page_number,
                time_taken=duration,
                success=False,
                retry_count=0,
                results_count=0,
                error=str(exc),
            )
            return metric, None

    def _build_search_url(
        self,
        *,
        page_number: int,
        query: str | None,
        location: str | None,
        radius: int | None,
        min_price: int | None,
        max_price: int | None,
        sort_by: str | None = None,
    ) -> str:
        from urllib.parse import urlencode

        params = {}
        if location:
            params["locationStr"] = location
        if radius:
            params["radius"] = radius

        # Build URL path following Kleinanzeigen pattern:
        # s-{first_modifier}/{other_modifiers}/{query}/k0
        # Examples:
        # - s-preis:10:350/mini-pc/k0
        # - s-preis:10:350/seite:2/mini-pc/k0
        # - s-sortierung:preis/preis:10:350/mini-pc/k0

        first_modifier = None
        path_segments = []

        # Determine the first modifier (goes after 's-')
        # Priority: sort > price (if no sort)
        if sort_by:
            if sort_by.lower() in ["price", "lowest", "preis"]:
                first_modifier = "sortierung:preis"
            elif sort_by.lower() in ["highest", "teuerste"]:
                first_modifier = "sortierung:teuerste"

        # If no sort, price becomes first modifier
        if not first_modifier and (min_price is not None or max_price is not None):
            min_segment = str(min_price) if min_price is not None else ""
            max_segment = str(max_price) if max_price is not None else ""
            first_modifier = f"preis:{min_segment}:{max_segment}"

        # Build the base path with 's' and first modifier
        # If no modifiers but we have a query, query becomes the first modifier
        if query:
            slugified_query = self._slugify(query)
        else:
            slugified_query = None

        if first_modifier:
            base_path = f"s-{first_modifier}"
        elif slugified_query:
            # If no other modifiers, query goes directly after s-
            base_path = f"s-{slugified_query}"
            slugified_query = None  # Don't add it again later
        else:
            base_path = "s"

        # Add remaining modifiers as separate segments
        # If sort was first, add price as second segment
        if sort_by and (min_price is not None or max_price is not None):
            min_segment = str(min_price) if min_price is not None else ""
            max_segment = str(max_price) if max_price is not None else ""
            path_segments.append(f"preis:{min_segment}:{max_segment}")

        # Add page number (seite:X)
        if page_number > 1:
            path_segments.append(f"seite:{page_number}")

        # Add query if it wasn't already added to base_path
        if slugified_query:
            path_segments.append(slugified_query)

        # Add k0 suffix
        path_segments.append("k0")

        # Construct final path
        if path_segments:
            full_path = f"{base_path}/{'/'.join(path_segments)}"
        else:
            full_path = f"{base_path}/k0"

        query_string = urlencode(params)
        base_url = f"{self.BASE_URL}/{full_path}"
        return f"{base_url}?{query_string}" if query_string else base_url

    @staticmethod
    def _slugify(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"\s+", "-", value)
        value = re.sub(r"[^a-z0-9-]", "", value)
        return value or "k0"

    @staticmethod
    def _extract_total_results(soup: BeautifulSoup) -> int | None:
        """Extract total results count from breadcrumb.

        Example: <span class="breadcrump-summary">1 - 25 von 3.006 Ergebnissen für „mini pc" in Deutschland</span>
        Extracts: 3006
        """
        breadcrumb = soup.select_one(".breadcrump-summary")
        if not breadcrumb:
            return None

        text = breadcrumb.get_text(strip=True)
        # Pattern: "X - Y von Z.ZZZ Ergebnissen" or "X - Y von Z Ergebnissen"
        # Need to handle German number format with dots as thousands separator
        match = re.search(r"von\s+([\d.]+)\s+Ergebnis", text)
        if not match:
            return None

        # Remove dots (thousands separator) and convert to int
        total_str = match.group(1).replace(".", "")
        try:
            return int(total_str)
        except ValueError:
            logger.warning(f"Failed to parse total results from: {text}")
            return None

    def _parse_listing_summary(self, article: Tag) -> ListingSummary | None:
        ad_id = article.get("data-adid")
        href = article.get("data-href")
        if not ad_id or not href:
            return None

        title_element = article.select_one("h2 a.ellipsis")
        price_element = article.select_one(
            "p.aditem-main--middle--price-shipping--price"
        )
        description_element = article.select_one("p.aditem-main--middle--description")

        price = parse_price(price_element.get_text() if price_element else None)

        summary_data: Dict[str, Any] = {
            "adid": ad_id,
            "url": f"{self.BASE_URL}{href}",
            "title": title_element.get_text(strip=True) if title_element else "",
            "price": price["amount"],
            "currency": price["currency"],
            "negotiable": price["negotiable"],
            "description": (
                description_element.get_text(strip=True)
                if description_element
                else None
            ),
        }
        return ListingSummary.model_validate(summary_data)

    def _parse_delivery_method(self, soup: BeautifulSoup) -> str | None:
        shipping_text = soup.select_one(".boxedarticle--details--shipping")
        if shipping_text is None:
            return None
        text = shipping_text.get_text(strip=True)
        if "Nur Abholung" in text:
            return "pickup"
        return "shipping" if "Versand" in text else None

    def _parse_delivery_cost(self, soup: BeautifulSoup) -> str | None:
        shipping_text = soup.select_one(".boxedarticle--details--shipping")
        if shipping_text is None:
            return None
        text = shipping_text.get_text(" ", strip=True)
        match = re.search(r"([0-9.,]+)\s*€", text)
        return f"{match[1]} €" if match else None

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        description = soup.select_one("#viewad-description-text")
        if not description:
            return None
        cleaned = description.get_text("\n", strip=True)
        return re.sub(r"\n{2,}", "\n", cleaned)

    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        return [
            tag.get_text(strip=True)
            for tag in soup.select("#viewad-configuration .checktag")
            if tag.get_text(strip=True)
        ]
