"""
Phase 1 — collect listing links from CarSensor search/index pages.
"""

from __future__ import annotations

import json
import logging
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.config import BASE_URL, LISTING_URLS, DELAY_BETWEEN_REQUESTS
from scraper.http import get_soup
from scraper.models import ListingPreview

log = logging.getLogger(__name__)


def extract_id_from_url(url: str) -> str:
    m = re.search(r"/detail/([^/]+)/", url)
    return m.group(1) if m else ""


def parse_listing_page(soup: BeautifulSoup) -> list[ListingPreview]:
    previews: list[ListingPreview] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "[]")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict):
            data = [data]
        for obj in data:
            if obj.get("@type") != "ItemList":
                continue
            for item in obj.get("itemListElement", []):
                raw_url = item.get("url", "")
                clean_url = re.sub(r"\?.*", "", raw_url)
                if not clean_url:
                    continue
                if not clean_url.startswith("http"):
                    clean_url = urljoin(BASE_URL, clean_url)
                images = item.get("image", [])
                first_img = images[0].get("url") if images else None
                first_desc = images[0].get("description") if images else None
                previews.append(ListingPreview(
                    detail_url=clean_url,
                    image=first_img,
                    description=first_desc,
                ))
    return previews


def collect_all_previews() -> list[ListingPreview]:
    all_previews: list[ListingPreview] = []
    seen: set[str] = set()
    for listing_url in LISTING_URLS:
        try:
            previews = parse_listing_page(get_soup(listing_url))
            log.info("  → %d cars found on %s", len(previews), listing_url)
            for p in previews:
                if p.detail_url not in seen:
                    seen.add(p.detail_url)
                    all_previews.append(p)
        except Exception as exc:
            log.warning("Failed listing page %s: %s", listing_url, exc)
        time.sleep(DELAY_BETWEEN_REQUESTS)
    log.info("Total unique listings: %d", len(all_previews))
    return all_previews
