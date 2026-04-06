"""
CarSensor.net scraper — orchestrator.

The heavy lifting now lives in focused modules:
  config.py      — URLs, headers, delays
  models.py      — CarDetail, ListingPreview dataclasses
  normalizers.py — Japanese→English value maps and normalizer functions
  http.py        — requests session + fetch helpers
  listing.py     — Phase 1: parse listing/index pages
  detail.py      — Phase 2: parse a single car detail page

This file owns only the orchestration logic (run_scraper) and
re-exports the symbols that save_to_db.py depends on so nothing else
needs to change.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Awaitable, Optional

from scraper.config import DELAY_BETWEEN_REQUESTS
from scraper.models import CarDetail, ListingPreview          # re-exported
from scraper.listing import collect_all_previews, extract_id_from_url
from scraper.detail import parse_detail_page
from scraper.http import fetch

log = logging.getLogger(__name__)


def scrape_detail(preview: ListingPreview) -> Optional[CarDetail]:
    try:
        car = parse_detail_page(preview.detail_url, fetch(preview.detail_url))
        log.info("  ✓ %s  %s %s %s", car.external_id, car.brand, car.model, car.year)
        return car
    except Exception as exc:
        log.warning("  ✗ %s — %s", preview.detail_url, exc)
        return None


async def run_scraper(
    live: bool = True,
    known_ids: set[str] | None = None,
    on_car_saved: Callable[[CarDetail], Awaitable[None]] | None = None,
) -> list[CarDetail]:
    if not live:
        return _run_offline()

    known_ids = known_ids or set()

    log.info("=== PHASE 1: collect listing links ===")
    previews = collect_all_previews()

    new_previews = [p for p in previews if extract_id_from_url(p.detail_url) not in known_ids]
    skipped = len(previews) - len(new_previews)
    log.info("Skipping %d already-known cars. Scraping %d new ones.", skipped, len(new_previews))

    log.info("=== PHASE 2: scrape detail pages ===")
    results: list[CarDetail] = []
    for i, preview in enumerate(new_previews, 1):
        log.info("[%d/%d] %s", i, len(new_previews), preview.detail_url)
        car = scrape_detail(preview)
        if car:
            results.append(car)
            if on_car_saved:
                await on_car_saved(car)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    log.info("Done. Scraped %d / %d new cars.", len(results), len(new_previews))
    return results


def _run_offline() -> list[CarDetail]:
    import os
    from bs4 import BeautifulSoup
    from scraper.listing import parse_listing_page

    log.info("=== OFFLINE MODE ===")
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(base, "..")

    with open(os.path.join(root, "outer.html"), encoding="utf-8") as f:
        previews = parse_listing_page(BeautifulSoup(f.read(), "html.parser"))
    log.info("Previews: %d", len(previews))

    with open(os.path.join(root, "detail.html"), encoding="utf-8") as f:
        car = parse_detail_page(
            "https://www.carsensor.net/usedcar/detail/AU6910982958/index.html",
            f.read(),
        )
    return [car]
