from __future__ import annotations

import re
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup
from bs4.element import Tag


def _clean_text(value: Optional[Union[str, Tag]]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, Tag):
        value = value.get_text()
    return re.sub(r"\s+", " ", value).strip()


def parse_price(price_text: Optional[str]) -> Dict[str, object]:
    if not price_text:
        return {"amount": 0.0, "currency": "EUR", "negotiable": False}

    negotiable = "VB" in price_text.upper()
    matches = re.findall(r"\d{1,3}(?:[.\s]\d{3})*(?:,\d+)?", price_text)
    amount = 0.0
    if matches:
        normalized = matches[0].replace(".", "").replace(" ", "").replace(",", ".")
        try:
            amount = float(normalized)
        except ValueError:
            amount = 0.0

    return {"amount": amount, "currency": "EUR", "negotiable": negotiable}


def parse_categories(soup: BeautifulSoup) -> List[str]:
    return [
        tag.get_text(strip=True)
        for tag in soup.select(".breadcrump-link")
        if tag.get_text(strip=True)
    ]


def parse_images(soup: BeautifulSoup) -> List[str]:
    images: List[str] = []
    for tag in soup.select("#viewad-image"):
        src = tag.get("src")
        if isinstance(src, str):
            images.append(src)
    return images


def parse_seller(soup: BeautifulSoup) -> Dict[str, object]:
    seller = {
        "name": _clean_text(
            soup.select_one(".userprofile-vip, .userprofile-header-user-name")
        ),
        "since": None,
        "type": "private",
        "badges": [],
    }

    for detail in soup.select(".userprofile-vip-details-text"):
        detail_text = detail.get_text(strip=True)
        if "Gewerblicher" in detail_text:
            seller["type"] = "business"
        if detail_text.startswith("Aktiv seit"):
            seller["since"] = detail_text.replace("Aktiv seit", "").strip()

    badges = [
        badge.get_text(strip=True)
        for badge in soup.select(".userprofile-vip-badges .userbadge-tag")
        if badge.get_text(strip=True)
    ]
    seller["badges"] = badges

    return seller


def parse_details(soup: BeautifulSoup) -> Dict[str, str]:
    details: Dict[str, str] = {}
    for item in soup.select("#viewad-details .addetailslist--detail"):
        parts = list(item.stripped_strings)
        if len(parts) >= 2:
            details[parts[0]] = parts[-1]
    return details


def parse_location(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    locality = soup.select_one("#viewad-locality")
    location_text = _clean_text(locality.get_text() if locality else None)
    if not location_text:
        return {"zip": "", "city": "", "state": None}

    parts = location_text.split(" ", 1)
    zip_code = parts[0]
    remainder = parts[1] if len(parts) > 1 else ""

    state = None
    city = remainder
    if " - " in remainder:
        state, city = [segment.strip() for segment in remainder.split(" - ", 1)]

    return {"zip": zip_code, "city": city.strip(), "state": state}


def parse_extra_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    created_at_element = soup.select_one("#viewad-extra-info span")
    created_at_text = created_at_element.get_text() if created_at_element else None
    return {"created_at": _clean_text(created_at_text)}
