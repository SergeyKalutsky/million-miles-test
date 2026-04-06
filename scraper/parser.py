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
from typing import Optional, Callable, Awaitable
from urllib.parse import urljoin

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

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Japanese value normalizers
# ---------------------------------------------------------------------------

def normalize_year(raw: str) -> Optional[int]:
    m = re.search(r"(\d{4})", raw or "")
    return int(m.group(1)) if m else None


def normalize_mileage_km(raw: str) -> Optional[int]:
    raw = (raw or "").replace(",", "").replace("，", "")
    m_man = re.search(r"([\d.]+)\s*万\s*km", raw)
    if m_man:
        return int(round(float(m_man.group(1)) * 10_000))
    m_plain = re.search(r"([\d.]+)\s*km", raw)
    if m_plain:
        return int(round(float(m_plain.group(1))))
    return None


def normalize_price_jpy(raw: str) -> Optional[int]:
    raw = (raw or "").replace(",", "").replace("，", "")
    m_man = re.search(r"([\d.]+)\s*万\s*円", raw)
    if m_man:
        return int(round(float(m_man.group(1)) * 10_000))
    m_plain = re.search(r"([\d]+)\s*円", raw)
    if m_plain:
        return int(m_plain.group(1))
    m_num = re.search(r"^([\d]+)$", raw.strip())
    if m_num:
        return int(m_num.group(1))
    return None


BRAND_MAP: dict[str, str] = {
    # Japanese domestic
    "トヨタ": "Toyota", "ホンダ": "Honda", "日産": "Nissan",
    "スバル": "Subaru", "マツダ": "Mazda", "三菱": "Mitsubishi",
    "スズキ": "Suzuki", "ダイハツ": "Daihatsu", "いすゞ": "Isuzu",
    "レクサス": "Lexus", "インフィニティ": "Infiniti", "アキュラ": "Acura",
    # German
    "メルセデス・ベンツ": "Mercedes-Benz", "メルセデスベンツ": "Mercedes-Benz",
    "BMW": "BMW", "アウディ": "Audi", "フォルクスワーゲン": "Volkswagen",
    "ポルシェ": "Porsche", "スマート": "Smart", "オペル": "Opel",
    # Italian
    "フィアット": "Fiat", "フェラーリ": "Ferrari", "ランボルギーニ": "Lamborghini",
    "マセラティ": "Maserati", "アルファ　ロメオ": "Alfa Romeo", "アルファロメオ": "Alfa Romeo",
    "アバルト": "Abarth", "ランチア": "Lancia",
    # British
    "ジャガー": "Jaguar", "ランドローバー": "Land Rover", "ミニ": "MINI",
    "ベントレー": "Bentley", "ロールスロイス": "Rolls-Royce", "マクラーレン": "McLaren",
    "ロータス": "Lotus", "アストンマーティン": "Aston Martin",
    # American
    "フォード": "Ford", "シボレー": "Chevrolet", "キャデラック": "Cadillac",
    "クライスラー": "Chrysler", "ジープ": "Jeep", "ダッジ": "Dodge",
    "リンカーン": "Lincoln", "ハマー": "Hummer", "テスラ": "Tesla",
    # French
    "プジョー": "Peugeot", "シトロエン": "Citroën", "ルノー": "Renault",
    # Swedish / Other
    "ボルボ": "Volvo", "サーブ": "Saab", "ヒュンダイ": "Hyundai", "キア": "Kia",
}

# Model names: Japanese katakana → English
MODEL_MAP: dict[str, str] = {
    # Alfa Romeo
    "ジュリア": "Giulia", "ジュリエッタ": "Giulietta", "ステルヴィオ": "Stelvio",
    "ミト": "MiTo", "スパイダー": "Spider", "ブレラ": "Brera",
    # Audi
    "クワトロ": "Quattro",
    # BMW
    "グランクーペ": "Gran Coupe", "グランツーリスモ": "Gran Turismo",
    # Ferrari
    "カリフォルニア": "California", "ポルトフィーノ": "Portofino",
    "ローマ": "Roma", "テスタロッサ": "Testarossa",
    # Lamborghini
    "ウラカン": "Huracán", "アヴェンタドール": "Aventador", "ウルス": "Urus",
    # Maserati
    "クワトロポルテ": "Quattroporte", "ギブリ": "Ghibli", "グランカブリオ": "GranCabrio",
    "グランツーリスモ": "GranTurismo", "レヴァンテ": "Levante",
    # Mercedes-Benz
    "マイバッハ": "Maybach",
    # Porsche
    "カイエン": "Cayenne", "マカン": "Macan", "パナメーラ": "Panamera",
    "タイカン": "Taycan", "ボクスター": "Boxster", "ケイマン": "Cayman",
    # Rolls-Royce
    "ファントム": "Phantom", "レイス": "Wraith", "ゴースト": "Ghost",
    "カリナン": "Cullinan", "ドーン": "Dawn",
    # Bentley
    "コンチネンタル": "Continental", "フライングスパー": "Flying Spur",
    "ベンテイガ": "Bentayga", "ミュルザンヌ": "Mulsanne",
    # General Japanese model names
    "プリウス": "Prius", "クラウン": "Crown", "カムリ": "Camry",
    "ランドクルーザー": "Land Cruiser", "ハイエース": "Hiace", "アルファード": "Alphard",
    "ヴェルファイア": "Vellfire", "ハリアー": "Harrier", "ヴォクシー": "Voxy",
    "シエンタ": "Sienta", "ヤリス": "Yaris", "アクア": "Aqua",
    "ノア": "Noah", "エスティマ": "Estima", "セルシオ": "Celsior",
    "スープラ": "Supra", "86": "86", "GR86": "GR86",
    "フィット": "Fit", "シビック": "Civic", "アコード": "Accord",
    "ステップワゴン": "Step WGN", "フリード": "Freed", "ヴェゼル": "Vezel",
    "エヌボックス": "N-BOX", "オデッセイ": "Odyssey", "レジェンド": "Legend",
    "スカイライン": "Skyline", "フェアレディＺ": "Fairlady Z", "フェアレディZ": "Fairlady Z",
    "ノート": "Note", "セレナ": "Serena", "エクストレイル": "X-Trail",
    "ジューク": "Juke", "キャラバン": "Caravan", "エルグランド": "Elgrand",
    "インプレッサ": "Impreza", "レガシィ": "Legacy", "フォレスター": "Forester",
    "アウトバック": "Outback", "レヴォーグ": "Levorg", "BRZ": "BRZ",
    "デミオ": "Demio", "アテンザ": "Atenza", "アクセラ": "Axela",
    "ＣＸ－５": "CX-5", "CX-5": "CX-5", "ＣＸ－３": "CX-3", "ロードスター": "Roadster",
    "アウトランダー": "Outlander", "エクリプスクロス": "Eclipse Cross",
    "パジェロ": "Pajero", "デリカ": "Delica",
    "ジムニー": "Jimny", "スイフト": "Swift", "ソリオ": "Solio",
    "ハスラー": "Hustler", "アルト": "Alto", "ワゴンＲ": "Wagon R",
    "ミラ": "Mira", "タント": "Tanto", "ムーヴ": "Move",
    "コペン": "Copen",
}

COLOR_MAP: dict[str, str] = {
    "ブラック": "Black", "黒": "Black",
    "ホワイト": "White", "白": "White",
    "シルバー": "Silver", "シルバーメタリック": "Silver",
    "グレー": "Gray", "グレイ": "Gray", "灰": "Gray",
    "レッド": "Red", "赤": "Red",
    "ブルー": "Blue", "青": "Blue",
    "ネイビー": "Navy",
    "グリーン": "Green", "緑": "Green",
    "ゴールド": "Gold", "金": "Gold",
    "ブラウン": "Brown", "茶": "Brown",
    "ベージュ": "Beige",
    "オレンジ": "Orange",
    "イエロー": "Yellow", "黄": "Yellow",
    "パープル": "Purple", "紫": "Purple",
    "ピンク": "Pink",
    "ワインレッド": "Wine Red", "バーガンディ": "Burgundy",
    "チャンパン": "Champagne",
    # compound / pearl / metallic variants
    "ホワイトパールクリスタルシャイン": "Pearl White",
    "クリスタルブラックパール": "Pearl Black",
    "グラファイトブラックガラスフレーク": "Graphite Black",
    "アイスホワイト": "Ice White",
    "パール": "Pearl White",
    "ミモザイエローパールメタリック": "Yellow Pearl",
    "ソニックシルバー": "Silver",
    "パールマイカ": "Pearl",
    "マスタードイエローマイカメタリック": "Mustard Yellow",
    "ブリリアントホワイトパール": "Brilliant White Pearl",
    "アッシュ": "Ash Gray",
    "ムーンライトブルーパールメタリック": "Blue Pearl",
    "ダークグレーメタリック": "Dark Gray",
    "プレミアムホワイトパールクリスタルシャイン": "Pearl White",
}

TRANSMISSION_MAP: dict[str, str] = {
    "フロアMTモード付CVT": "CVT", "CVT": "CVT", "セミAT": "Semi-AT",
    "デュアルクラッチ": "DCT", "2ペダルMT": "2-pedal MT", "AT": "AT", "MT": "MT",
}

FUEL_MAP: dict[str, str] = {
    "ガソリン": "gasoline", "ディーゼル": "diesel", "ハイブリッド": "hybrid",
    "電気": "electric", "プラグインハイブリッド": "PHEV", "水素": "hydrogen", "LPG": "LPG",
}

BODY_MAP: dict[str, str] = {
    "ステーションワゴン": "station wagon", "ミニバン/ワンボックス": "minivan",
    "SUV/クロカン": "SUV", "クロカン・ＳＵＶ": "SUV", "クロカン": "SUV",
    "軽トラック/軽バン": "kei truck/van",
    "セダン": "sedan", "ハッチバック": "hatchback", "コンパクト": "compact",
    "ミニバン": "minivan", "SUV": "SUV", "クーペ": "coupe",
    "オープンカー": "convertible", "軽自動車": "kei car",
    "トラック/バン": "truck/van", "バス": "bus",
}


def map_brand(ja: str) -> str:
    return BRAND_MAP.get(ja.strip(), ja.strip())

def map_model(ja: str) -> str:
    """Map Japanese model name to English. Falls back to original string."""
    return MODEL_MAP.get(ja.strip(), ja.strip())

def map_transmission(ja: str) -> str:
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

def map_color(ja: str) -> str:
    """Translate Japanese color string to English. Tries longest match first."""
    ja = ja.strip()
    # Try exact match first
    if ja in COLOR_MAP:
        return COLOR_MAP[ja]
    # Try longest prefix/substring match
    for k in sorted(COLOR_MAP, key=len, reverse=True):
        if k in ja:
            return COLOR_MAP[k]
    return ja


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
    raw_text: Optional[str] = None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_session = requests.Session()
_session.headers.update(HEADERS)


def fetch(url: str, timeout: int = 20) -> str:
    log.info("GET %s", url)
    resp = _session.get(url, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def get_soup(url: str) -> BeautifulSoup:
    return BeautifulSoup(fetch(url), "html.parser")


# ---------------------------------------------------------------------------
# Phase 1 — Listing pages
# ---------------------------------------------------------------------------

def extract_id_from_url(url: str) -> str:
    m = re.search(r"/detail/([^/]+)/", url)
    return m.group(1) if m else ""


def parse_listing_json(soup: BeautifulSoup) -> list[ListingPreview]:
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
                previews.append(ListingPreview(detail_url=clean_url, image=first_img, description=first_desc))
    return previews


def collect_all_previews() -> list[ListingPreview]:
    all_previews: list[ListingPreview] = []
    seen: set[str] = set()
    for listing_url in LISTING_URLS:
        try:
            previews = parse_listing_json(get_soup(listing_url))
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
    return tag.get_text(strip=True) if tag else ""


def _th_td_map(soup: BeautifulSoup) -> dict[str, str]:
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


def parse_detail_page(url: str, html: str) -> CarDetail:
    soup = BeautifulSoup(html, "html.parser")
    external_id = extract_id_from_url(url)

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

    td_map = _th_td_map(soup)

    brand_ja: Optional[str] = None
    model_ja: Optional[str] = None
    ld_brands = product_json.get("brand", [])
    if isinstance(ld_brands, list) and len(ld_brands) >= 1:
        brand_ja = ld_brands[0].get("name")
    if isinstance(ld_brands, list) and len(ld_brands) >= 2:
        model_ja = ld_brands[1].get("name")
    if not brand_ja:
        parts = product_json.get("name", "").split()
        if parts:
            brand_ja = parts[0]
        if len(parts) >= 2:
            model_ja = parts[1]
    brand = map_brand(brand_ja) if brand_ja else None
    model = map_model(model_ja) if model_ja else None

    price_jpy: Optional[int] = None
    offers = product_json.get("offers", [])
    if isinstance(offers, list) and offers:
        price_jpy = normalize_price_jpy(str(offers[0].get("price", "")))
    elif isinstance(offers, dict):
        price_jpy = normalize_price_jpy(str(offers.get("price", "")))

    year = normalize_year(td_map.get("年式") or td_map.get("年式初度登録年") or "")
    mileage_km = normalize_mileage_km(td_map.get("走行距離", ""))
    transmission = map_transmission(td_map.get("ミッション", "")) if td_map.get("ミッション") else None
    fuel_type = map_fuel(td_map.get("エンジン種別", "")) if td_map.get("エンジン種別") else None
    body_type = map_body(td_map.get("ボディタイプ", "")) if td_map.get("ボディタイプ") else None
    color_raw = td_map.get("色") or product_json.get("color") or ""
    color = map_color(str(color_raw)) if color_raw else None
    location = td_map.get("地域") or None

    photos: list[str] = []
    for a in soup.select("a.js-photo[data-photo]"):
        photo_url = a.get("data-photo", "")
        if photo_url and str(photo_url).startswith("http") and photo_url not in photos:
            photos.append(str(photo_url))
    og_img = soup.find("meta", property="og:image")
    if og_img:
        og_url = og_img.get("content", "")
        if og_url and str(og_url).startswith("http") and og_url not in photos:
            photos.insert(0, str(og_url))

    return CarDetail(
        external_id=external_id, source_url=url, brand=brand, model=model,
        year=year, mileage_km=mileage_km, price_jpy=price_jpy,
        transmission=transmission, fuel_type=fuel_type, body_type=body_type,
        color=color, location=location, photos=photos,
        raw_json=product_json or None,
        raw_text=soup.get_text(separator="\n", strip=True)[:4000],
    )


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
        log.info("=== OFFLINE MODE ===")
        import os
        base = os.path.dirname(os.path.abspath(__file__))
        outer = os.path.join(base, "..", "outer.html")
        detail = os.path.join(base, "..", "detail.html")
        with open(outer, encoding="utf-8") as f:
            previews = parse_listing_json(BeautifulSoup(f.read(), "html.parser"))
        log.info("Previews: %d", len(previews))
        with open(detail, encoding="utf-8") as f:
            car = parse_detail_page(
                "https://www.carsensor.net/usedcar/detail/AU6910982958/index.html",
                f.read(),
            )
        return [car]

    known_ids = known_ids or set()

    log.info("=== PHASE 1: collect listing links ===")
    previews = collect_all_previews()

    # Filter out cars we already have in the DB
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
