"""
CarSensor.net scraper
Phase 1: collect listing links + preview data from 10 pages
Phase 2: scrape each detail page for full car fields
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://www.carsensor.net"

LISTING_URLS = [
    "https://www.carsensor.net/usedcar/search.php?SKIND=1",  # page 1
    *[f"https://www.carsensor.net/usedcar/index{i}.html" for i in range(2, 11)],  # pages 2-10
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
}

DELAY_BETWEEN_REQUESTS = 1.5  # seconds — be polite

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Japanese value normalizers
# ---------------------------------------------------------------------------

# 年式: "2021(R03)" → 2021, "2020(R02)" → 2020
def normalize_year(raw: str) -> Optional[int]:
    m = re.search(r"(\d{4})", raw or "")
    return int(m.group(1)) if m else None


# 走行距離: "3.9万km" → 39000, "6.9万km" → 69000, "10km" → 10
def normalize_mileage_km(raw: str) -> Optional[int]:
    raw = (raw or "").replace(",", "").replace("，", "")
    m_man = re.search(r"([\d.]+)\s*万\s*km", raw)
    if m_man:
        return int(round(float(m_man.group(1)) * 10_000))
    m_plain = re.search(r"([\d.]+)\s*km", raw)
    if m_plain:
        return int(round(float(m_plain.group(1))))
    return None


# 価格: "193.3万円" → 1933000, "133.8万円" → 1338000
def normalize_price_jpy(raw: str) -> Optional[int]:
    raw = (raw or "").replace(",", "").replace("，", "")
    m_man = re.search(r"([\d.]+)\s*万\s*円", raw)
    if m_man:
        return int(round(float(m_man.group(1)) * 10_000))
    m_plain = re.search(r"([\d]+)\s*円", raw)
    if m_plain:
        return int(m_plain.group(1))
    # ld+json price is already in yen as a plain number string
    m_num = re.search(r"^([\d]+)$", raw.strip())
    if m_num:
        return int(m_num.group(1))
    return None


# Brand / model mapping (Japanese → English)
BRAND_MAP: dict[str, str] = {
    "トヨタ": "Toyota",
    "ホンダ": "Honda",
    "日産": "Nissan",
    "スバル": "Subaru",
    "マツダ": "Mazda",
    "三菱": "Mitsubishi",
    "スズキ": "Suzuki",
    "ダイハツ": "Daihatsu",
    "いすゞ": "Isuzu",
    "メルセデス・ベンツ": "Mercedes-Benz",
    "BMW": "BMW",
    "アウディ": "Audi",
    "フォルクスワーゲン": "Volkswagen",
    "フォード": "Ford",
    "フィアット": "Fiat",
    "スマート": "Smart",
    "ポルシェ": "Porsche",
    "レクサス": "Lexus",
    "マクラーレン": "McLaren",
    "ランボルギーニ": "Lamborghini",
    "フェラーリ": "Ferrari",
}

TRANSMISSION_MAP: dict[str, str] = {
    "AT": "AT",
    "MT": "MT",
    "CVT": "CVT",
    "フロアMTモード付CVT": "CVT",
    "セミAT": "Semi-AT",
    "デュアルクラッチ": "DCT",
    "2ペダルMT": "2-pedal MT",
}

FUEL_MAP: dict[str, str] = {
    "ガソリン": "gasoline",
    "ディーゼル": "diesel",
    "ハイブリッド": "hybrid",
    "電気": "electric",
    "プラグインハイブリッド": "PHEV",
    "水素": "hydrogen",
    "LPG": "LPG",
}

BODY_MAP: dict[str, str] = {
    "セダン": "sedan",
    "ハッチバック": "hatchback",
    "コンパクト": "compact",
    "ステーションワゴン": "station wagon",
    "ミニバン/ワンボックス": "minivan",
    "ミニバン": "minivan",
    "SUV/クロカン": "SUV",
    "SUV": "SUV",
    "クーペ": "coupe",
    "オープンカー": "convertible",
    "軽自動車": "kei car",
    "軽トラック/軽バン": "kei truck/van",
    "トラック/バン": "truck/van",
    "バス": "bus",
}


def map_brand(ja: str) -> str:
    return BRAND_MAP.get(ja.strip(), ja.strip())


def map_transmission(ja: str) -> str:
    # Match longest key first to avoid "MT" matching inside "フロアMTモード付CVT"
    for k in sorted(TRANSMISSION_MAP, key=len, reverse=True):
        if k in ja:
            return TRANSMISSION_MAP[k]
    return ja.strip()


def map_fuel(ja: str) -> str:
    return FUEL_MAP.get(ja.strip(), ja.strip())


def map_body(ja: str) -> str:
    for k, v in BODY_MAP.items():
        if k in ja:
            return v
    return ja.strip()


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ListingPreview:
    detail_url: str
    image: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CarDetail:
    external_id: str
    source_url: str
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    price_jpy: Optional[int] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    location: Optional[str] = None
    photos: list[str] = field(default_factory=list)
    raw_json: Optional[dict] = None
    raw_text: Optional[str] = None  # first 4000 chars of page text


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

session = requests.Session()
session.headers.update(HEADERS)


def fetch(url: str, timeout: int = 20) -> str:
    log.info("GET %s", url)
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def get_soup(url: str) -> BeautifulSoup:
    html = fetch(url)
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Phase 1 — Listing pages
# ---------------------------------------------------------------------------

def extract_id_from_url(url: str) -> str:
    """Extract AU6910982958 from detail URL."""
    m = re.search(r"/detail/([^/]+)/", url)
    return m.group(1) if m else ""


def parse_listing_json(soup: BeautifulSoup) -> list[ListingPreview]:
    """Find script[type='application/ld+json'], pick the ItemList block."""
    previews: list[ListingPreview] = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "[]")
        except (json.JSONDecodeError, TypeError):
            continue

        # data can be a list of objects or a single object
        if isinstance(data, dict):
            data = [data]

        for obj in data:
            if obj.get("@type") != "ItemList":
                continue
            for item in obj.get("itemListElement", []):
                raw_url = item.get("url", "")
                # strip tracking params — keep only the canonical path
                clean_url = re.sub(r"\?.*", "", raw_url)
                if not clean_url:
                    continue
                if not clean_url.startswith("http"):
                    clean_url = urljoin(BASE_URL, clean_url)

                # first image
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
            soup = get_soup(listing_url)
            previews = parse_listing_json(soup)
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


# ---------------------------------------------------------------------------
# Phase 2 — Detail pages
# ---------------------------------------------------------------------------

def _text(tag) -> str:
    """Get stripped text from a BeautifulSoup tag."""
    return tag.get_text(strip=True) if tag else ""


def _th_td_map(soup: BeautifulSoup) -> dict[str, str]:
    """
    Build a flat dict of {header_text: cell_text} from all defaultTable rows.
    Headers can have <a>, <i> children — we strip those.
    """
    result: dict[str, str] = {}
    for table in soup.select("table.defaultTable__table"):
        for row in table.find_all("tr"):
            heads = row.find_all("th", class_="defaultTable__head")
            tds = row.find_all("td", class_="defaultTable__description")
            for th, td in zip(heads, tds):
                key = th.get_text(separator="", strip=True)
                # drop "(初度登録年)" style suffixes
                key = re.sub(r"[（(][^）)]*[）)]", "", key).strip()
                val = td.get_text(separator=" ", strip=True)
                if key:
                    result[key] = val
    return result


def parse_detail_page(url: str, html: str) -> CarDetail:
    soup = BeautifulSoup(html, "html.parser")

    # --- external_id from URL ------------------------------------------
    external_id = extract_id_from_url(url)

    # --- ld+json Product block -----------------------------------------
    product_json: dict = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "[]")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict):
            data = [data]
        for obj in data:
            if obj.get("@type") == "Product":
                product_json = obj
                break

    # --- th→td map for the spec tables --------------------------------
    td_map = _th_td_map(soup)

    # --- Brand & model -------------------------------------------------
    brand_ja: Optional[str] = None
    model_ja: Optional[str] = None

    # Try ld+json "brand" array first: [{"@type":"Thing","name":"スバル"}, {"@type":"Thing","name":"レヴォーグ"}]
    ld_brands = product_json.get("brand", [])
    if isinstance(ld_brands, list) and len(ld_brands) >= 1:
        brand_ja = ld_brands[0].get("name")
    if isinstance(ld_brands, list) and len(ld_brands) >= 2:
        model_ja = ld_brands[1].get("name")

    # Fallback: parse from og:title or product name
    if not brand_ja:
        product_name = product_json.get("name", "")
        # "スバル レヴォーグ 1.8 GT-H EX 4WD ..."
        parts = product_name.split()
        if parts:
            brand_ja = parts[0]
        if len(parts) >= 2:
            model_ja = parts[1]

    brand = map_brand(brand_ja) if brand_ja else None

    # --- Price ---------------------------------------------------------
    price_jpy: Optional[int] = None
    offers = product_json.get("offers", [])
    if isinstance(offers, list) and offers:
        price_jpy = normalize_price_jpy(str(offers[0].get("price", "")))
    elif isinstance(offers, dict):
        price_jpy = normalize_price_jpy(str(offers.get("price", "")))

    # --- Year ----------------------------------------------------------
    year_raw = td_map.get("年式") or td_map.get("年式初度登録年") or ""
    # specWrap shows "2021" directly; table shows "2021(R03)"
    year = normalize_year(year_raw)
    if not year:
        # Try specWrap__box__num next to 年式 label
        spec_year_tag = soup.select_one("p.specWrap__box__title:-soup-contains('年式')")
        if spec_year_tag:
            num_tag = spec_year_tag.find_next_sibling("p", class_="specWrap__box__num")
            if num_tag:
                year = normalize_year(_text(num_tag))

    # --- Mileage -------------------------------------------------------
    mileage_raw = td_map.get("走行距離", "")
    mileage_km = normalize_mileage_km(mileage_raw)
    if not mileage_km:
        spec_km_tag = soup.select_one(".specWrap__box__title:-soup-contains('走行距離')")
        if spec_km_tag:
            num = spec_km_tag.find_next_sibling("p", class_="specWrap__box__num")
            unit = spec_km_tag.find_next_sibling("p", class_="specWrap__boxUnit")
            if num and unit:
                mileage_km = normalize_mileage_km(_text(num) + _text(unit))

    # --- Transmission --------------------------------------------------
    transmission_ja = td_map.get("ミッション", "")
    transmission = map_transmission(transmission_ja) if transmission_ja else None

    # --- Fuel type -----------------------------------------------------
    fuel_ja = td_map.get("エンジン種別", "")
    fuel_type = map_fuel(fuel_ja) if fuel_ja else None

    # --- Body type -----------------------------------------------------
    body_ja = td_map.get("ボディタイプ", "")
    body_type = map_body(body_ja) if body_ja else None

    # --- Color ---------------------------------------------------------
    color = td_map.get("色") or product_json.get("color")

    # --- Location ------------------------------------------------------
    location_raw = td_map.get("地域", "")
    if not location_raw:
        spec_loc = soup.select_one(".specWrap__box__title:-soup-contains('地域')")
        if spec_loc:
            detail_tag = spec_loc.find_next_sibling("p", class_="specWrap__boxDetail")
            location_raw = _text(detail_tag)
    location = location_raw or None

    # --- Photos --------------------------------------------------------
    photos: list[str] = []
    for a in soup.select("a.js-photo[data-photo]"):
        photo_url = a.get("data-photo", "")
        # Skip site assets (relative paths or non-photo CDN paths)
        if photo_url and photo_url.startswith("http") and photo_url not in photos:
            photos.append(photo_url)
    # Also pick up og:image as the hero shot
    og_img = soup.find("meta", property="og:image")
    if og_img:
        og_url = og_img.get("content", "")
        if og_url and og_url.startswith("http") and og_url not in photos:
            photos.insert(0, og_url)

    # --- raw_text (trimmed) -------------------------------------------
    body_text = soup.get_text(separator="\n", strip=True)
    raw_text = body_text[:4000]

    return CarDetail(
        external_id=external_id,
        source_url=url,
        brand=brand,
        model=model_ja,
        year=year,
        mileage_km=mileage_km,
        price_jpy=price_jpy,
        transmission=transmission,
        fuel_type=fuel_type,
        body_type=body_type,
        color=color,
        location=location,
        photos=photos,
        raw_json=product_json or None,
        raw_text=raw_text,
    )


def scrape_detail(preview: ListingPreview) -> Optional[CarDetail]:
    try:
        html = fetch(preview.detail_url)
        car = parse_detail_page(preview.detail_url, html)
        log.info("  ✓ %s  %s %s %s  ¥%s",
                 car.external_id, car.brand, car.model, car.year,
                 f"{car.price_jpy:,}" if car.price_jpy else "?")
        return car
    except Exception as exc:
        log.warning("  ✗ %s — %s", preview.detail_url, exc)
        return None


# ---------------------------------------------------------------------------
# Offline helpers (parse from saved HTML files for dev/testing)
# ---------------------------------------------------------------------------

def parse_listing_from_file(path: str) -> list[ListingPreview]:
    with open(path, encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    return parse_listing_json(soup)


def parse_detail_from_file(path: str, url: str = "https://www.carsensor.net/usedcar/detail/LOCAL/index.html") -> CarDetail:
    with open(path, encoding="utf-8") as f:
        html = f.read()
    return parse_detail_page(url, html)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_scraper(live: bool = True) -> list[CarDetail]:
    """
    live=True  → fetch from the web
    live=False → parse from local outer.html + detail.html for quick testing
    """
    if not live:
        log.info("=== OFFLINE MODE ===")
        previews = parse_listing_from_file("outer.html")
        log.info("Previews from outer.html: %d", len(previews))
        car = parse_detail_from_file(
            "detail.html",
            "https://www.carsensor.net/usedcar/detail/AU6910982958/index.html",
        )
        log.info("Detail from detail.html: %s", asdict(car))
        return [car]

    log.info("=== PHASE 1: collect listing links ===")
    previews = collect_all_previews()

    log.info("=== PHASE 2: scrape detail pages ===")
    results: list[CarDetail] = []
    for i, preview in enumerate(previews, 1):
        log.info("[%d/%d] %s", i, len(previews), preview.detail_url)
        car = scrape_detail(preview)
        if car:
            results.append(car)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    log.info("Done. Scraped %d / %d cars.", len(results), len(previews))
    return results


if __name__ == "__main__":
    import sys

    # Pass --live to actually hit the network; default is offline test
    live_mode = "--live" in sys.argv
    cars = run_scraper(live=live_mode)

    # Pretty-print first result
    if cars:
        print("\n=== Sample result ===")
        sample = asdict(cars[0])
        sample.pop("raw_text", None)      # too verbose for console
        sample.pop("raw_json", None)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
