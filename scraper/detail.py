"""
Phase 2 — parse a single car detail page into a CarDetail.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from scraper.models import CarDetail
from scraper.normalizers import (
    normalize_year, normalize_mileage_km, normalize_price_jpy,
    map_brand, map_model, map_transmission, map_fuel, map_body, map_color,
)

log = logging.getLogger(__name__)


def _extract_id(url: str) -> str:
    m = re.search(r"/detail/([^/]+)/", url)
    return m.group(1) if m else ""


def _th_td_map(soup: BeautifulSoup) -> dict[str, str]:
    """Extract all th→td pairs from the spec tables."""
    result: dict[str, str] = {}
    for table in soup.select("table.defaultTable__table"):
        for row in table.find_all("tr"):
            heads = row.find_all("th", class_="defaultTable__head")
            tds = row.find_all("td", class_="defaultTable__description")
            for th, td in zip(heads, tds):
                key = re.sub(r"[（(][^）)]*[）)]", "", th.get_text(separator="", strip=True)).strip()
                val = td.get_text(separator=" ", strip=True)
                if key:
                    result[key] = val
    return result


def _extract_product_json(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "[]")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict):
            data = [data]
        for obj in data:
            if obj.get("@type") == "Product":
                return obj
    return {}


def _extract_photos(soup: BeautifulSoup) -> list[str]:
    photos: list[str] = []
    for a in soup.select("a.js-photo[data-photo]"):
        url = a.get("data-photo", "")
        if url and str(url).startswith("http") and url not in photos:
            photos.append(str(url))
    og = soup.find("meta", property="og:image")
    if og:
        og_url = og.get("content", "")
        if og_url and str(og_url).startswith("http") and og_url not in photos:
            photos.insert(0, str(og_url))
    return photos


def _extract_brand_model(product_json: dict) -> tuple[Optional[str], Optional[str]]:
    brand_ja: Optional[str] = None
    model_ja: Optional[str] = None
    ld_brands = product_json.get("brand", [])
    if isinstance(ld_brands, list):
        if len(ld_brands) >= 1:
            brand_ja = ld_brands[0].get("name")
        if len(ld_brands) >= 2:
            model_ja = ld_brands[1].get("name")
    if not brand_ja:
        parts = product_json.get("name", "").split()
        if parts:
            brand_ja = parts[0]
        if len(parts) >= 2:
            model_ja = parts[1]
    return brand_ja, model_ja


def _extract_price(product_json: dict) -> Optional[int]:
    offers = product_json.get("offers", [])
    if isinstance(offers, list) and offers:
        return normalize_price_jpy(str(offers[0].get("price", "")))
    if isinstance(offers, dict):
        return normalize_price_jpy(str(offers.get("price", "")))
    return None


def parse_detail_page(url: str, html: str) -> CarDetail:
    soup = BeautifulSoup(html, "html.parser")
    product_json = _extract_product_json(soup)
    td_map = _th_td_map(soup)

    brand_ja, model_ja = _extract_brand_model(product_json)
    brand = map_brand(brand_ja) if brand_ja else None
    model = map_model(model_ja) if model_ja else None

    color_raw = td_map.get("色") or product_json.get("color") or ""

    return CarDetail(
        external_id=_extract_id(url),
        source_url=url,
        brand=brand,
        model=model,
        year=normalize_year(td_map.get("年式") or td_map.get("年式初度登録年") or ""),
        mileage_km=normalize_mileage_km(td_map.get("走行距離", "")),
        price_jpy=_extract_price(product_json),
        transmission=map_transmission(td_map["ミッション"]) if td_map.get("ミッション") else None,
        fuel_type=map_fuel(td_map["エンジン種別"]) if td_map.get("エンジン種別") else None,
        body_type=map_body(td_map["ボディタイプ"]) if td_map.get("ボディタイプ") else None,
        color=map_color(str(color_raw)) if color_raw else None,
        location=td_map.get("地域") or None,
        photos=_extract_photos(soup),
        raw_json=product_json or None,
        raw_text=soup.get_text(separator="\n", strip=True)[:4000],
    )
