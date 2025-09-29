from typing import Dict, List, Optional, Union, Any
from bs4 import BeautifulSoup


def get_element_content(
    soup: BeautifulSoup, selector: str, default: Any = None
) -> Optional[str]:
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else default


def get_elements_content(soup: BeautifulSoup, selector: str) -> List[str]:
    elements = soup.select(selector)
    return [element.get_text(strip=True) for element in elements]


def get_image_sources(soup: BeautifulSoup, selector: str) -> List[str]:
    images: List[str] = []
    image_element = soup.select_one(selector)
    if image_element and image_element.has_attr("src"):
        images.append(image_element["src"])
    return images


def parse_price(price_text: Optional[str]) -> Dict[str, Union[str, bool]]:
    if not price_text:
        return {"amount": "0", "currency": "€", "negotiable": False}

    price_text = price_text.strip()
    negotiable: bool = "VB" in price_text

    price_text = price_text.replace("VB", "").strip()

    amount: str = price_text.replace("€", "").replace(".", "").replace(",", ".").strip()

    return {"amount": amount, "currency": "€", "negotiable": negotiable}


def get_seller_details(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    result = {"name": None, "since": None, "type": "private", "badges": []}
    try:
        _get_seller_details_(soup, result)
    except Exception as exc:
        print(f"Error getting seller details: {str(exc)}")
    return result


def _get_seller_details_(soup, result):
    result["name"] = get_element_content(soup, ".userprofile-vip")

    for detail_element in soup.select(".userprofile-vip-details-text"):
        detail_text = detail_element.get_text(strip=True)
        if "Gewerblicher" in detail_text:
            result["type"] = "business"
        if detail_text.startswith("Aktiv seit"):
            result["since"] = detail_text.replace("Aktiv seit", "").strip()

    badges_selector = ".userprofile-vip-badges .userbadge-tag"
    badges = get_elements_content(soup, badges_selector)
    result["badges"] = [badge.strip() for badge in badges if badge and badge.strip()]


def get_details(soup: BeautifulSoup) -> Dict[str, str]:
    details: Dict[str, str] = {}
    try:
        detail_items = soup.select("#viewad-details .addetailslist--detail")
        for item in detail_items:
            parts = list(item.stripped_strings)
            if len(parts) >= 2:
                label = parts[0]
                value = parts[-1]
                details[label] = value
    except Exception as e:
        print(f"Error getting details: {str(e)}")
    return details


def get_features(soup: BeautifulSoup) -> List[str]:
    features: List[str] = []
    try:
        feature_elements = soup.select("#viewad-configuration .checktaglist .checktag")
        for feature in feature_elements:
            if feature_text := feature.get_text(strip=True):
                features.append(feature_text)
    except Exception as e:
        print(f"Error getting features: {str(e)}")
    return features


def get_location(soup: BeautifulSoup) -> Dict[str, str]:
    location_text = get_element_content(soup, "#viewad-locality")
    if not location_text:
        return {"zip": "", "city": "", "state": ""}

    zip_code, remainder = (location_text.split(" ", 1) + [""])[:2]
    city = remainder.strip()
    state = ""

    if " - " in remainder:
        state_part, city_part = remainder.split(" - ", 1)
        state = state_part.strip()
        city = city_part.strip()

    return {"zip": zip_code, "city": city, "state": state}


def get_extra_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {"created_at": None}
    try:
        if date_element := soup.select_one(
            "#viewad-extra-info > div:nth-child(1) > span"
        ):
            result["created_at"] = date_element.get_text(strip=True)

    except Exception as e:
        print(f"Error getting extra info: {str(e)}")
    return result
