"""
Scraper configuration — URLs, headers, delays.
"""

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
