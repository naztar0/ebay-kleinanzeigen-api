"""Unit tests for detail_parser — pure functions, no network."""

from __future__ import annotations

from bs4 import BeautifulSoup

from src.app.services.parsers.detail_parser import (
    parse_categories,
    parse_details,
    parse_extra_info,
    parse_images,
    parse_location,
    parse_price,
    parse_seller,
)
from tests.html_fixtures import DETAIL_PAGE_BUSINESS_HTML, DETAIL_PAGE_HTML


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestParsePrice:
    def test_integer_price(self):
        result = parse_price("299 €")
        assert result["amount"] == 299.0
        assert result["currency"] == "EUR"
        assert result["negotiable"] is False

    def test_negotiable_flag(self):
        result = parse_price("150 € VB")
        assert result["amount"] == 150.0
        assert result["negotiable"] is True

    def test_german_decimal(self):
        assert parse_price("149,99 €")["amount"] == 149.99

    def test_thousands_separator(self):
        assert parse_price("1.500 €")["amount"] == 1500.0

    def test_none_returns_zero(self):
        result = parse_price(None)
        assert result["amount"] == 0.0
        assert result["negotiable"] is False

    def test_empty_string_returns_zero(self):
        assert parse_price("")["amount"] == 0.0

    def test_free_listing_no_numeric(self):
        result = parse_price("Zu verschenken")
        assert result["amount"] == 0.0
        assert result["negotiable"] is False

    def test_vb_only_no_amount(self):
        result = parse_price("VB")
        assert result["negotiable"] is True
        assert result["amount"] == 0.0

    def test_large_price_with_decimal(self):
        result = parse_price("2.499,00 €")
        assert result["amount"] == 2499.0


class TestParseLocation:
    def _loc_soup(self, text: str) -> BeautifulSoup:
        return _soup(f'<span id="viewad-locality">{text}</span>')

    def test_zip_and_city(self):
        result = parse_location(self._loc_soup("10115 Berlin"))
        assert result["zip"] == "10115"
        assert result["city"] == "Berlin"
        assert result["state"] is None

    def test_zip_city_state(self):
        result = parse_location(self._loc_soup("80331 Bayern - München"))
        assert result["zip"] == "80331"
        assert result["state"] == "Bayern"
        assert result["city"] == "München"

    def test_missing_locality_element(self):
        result = parse_location(_soup("<html/>"))
        assert result["zip"] == ""
        assert result["city"] == ""
        assert result["state"] is None

    def test_real_fixture(self):
        result = parse_location(_soup(DETAIL_PAGE_HTML))
        assert result["zip"] == "10115"
        assert result["state"] == "Berlin"
        assert result["city"] == "Mitte"


class TestParseCategories:
    def test_extracts_links(self):
        assert parse_categories(_soup(DETAIL_PAGE_HTML)) == ["Elektronik", "Laptops"]

    def test_empty_when_none(self):
        assert parse_categories(_soup("<html/>")) == []


class TestParseImages:
    def test_multiple_images(self):
        images = parse_images(_soup(DETAIL_PAGE_HTML))
        assert len(images) == 2
        assert all(url.startswith("https://") for url in images)

    def test_empty_when_none(self):
        assert parse_images(_soup("<html/>")) == []


class TestParseSeller:
    def test_private_seller(self):
        result = parse_seller(_soup(DETAIL_PAGE_HTML))
        assert result["name"] == "max_user"
        assert result["type"] == "private"
        assert result["since"] == "2020"
        assert result["badges"] == []

    def test_business_seller(self):
        result = parse_seller(_soup(DETAIL_PAGE_BUSINESS_HTML))
        assert result["type"] == "business"
        assert result["since"] == "2018"
        assert result["name"] == "TechShop GmbH"

    def test_missing_seller_element(self):
        result = parse_seller(_soup("<html/>"))
        assert result["name"] is None
        assert result["type"] == "private"


class TestParseDetails:
    def test_key_value_pairs(self):
        result = parse_details(_soup(DETAIL_PAGE_HTML))
        assert result["Zustand"] == "Gebraucht"
        assert result["Marke"] == "Dell"

    def test_empty_when_none(self):
        assert parse_details(_soup("<html/>")) == {}


class TestParseExtraInfo:
    def test_created_at(self):
        result = parse_extra_info(_soup(DETAIL_PAGE_HTML))
        assert result["created_at"] == "Gestern, 14:32"

    def test_none_when_missing(self):
        result = parse_extra_info(_soup("<html/>"))
        assert result["created_at"] is None
