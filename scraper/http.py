"""
HTTP session and fetch helpers.
"""

from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

from scraper.config import HEADERS

log = logging.getLogger(__name__)

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
