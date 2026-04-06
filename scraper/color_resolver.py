"""
Color resolver: Japanese color string → English.

Strategy:
  1. Check static COLOR_MAP first (instant, exact/substring match).
  2. If still Japanese, convert katakana → romaji via pykakasi and
     title-case it. Ugly names become readable:
     テレーンカーキマイカメタリック → "Teren Kaki Maika Metarikku"
     which is at least sortable/filterable in the UI.
  3. Already-ASCII strings pass through unchanged.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from functools import lru_cache

from scraper.normalizers import map_color as _static_map_color

log = logging.getLogger(__name__)

_kks = None


def _get_kks():
    global _kks
    if _kks is None:
        import pykakasi
        _kks = pykakasi.kakasi()
    return _kks


@lru_cache(maxsize=512)
def _katakana_to_romaji(ja: str) -> str:
    result = _get_kks().convert(ja)
    parts = [item["hepburn"] for item in result]
    romaji = " ".join(parts)
    romaji = re.sub(r"\s+", " ", romaji).strip()
    return romaji.title()


def _has_japanese(text: str) -> bool:
    return any(unicodedata.category(c) == "Lo" for c in text)


def resolve_color(ja: str) -> str:
    """
    Translate a Japanese color string to English.
    Uses static map first, then romaji transliteration as fallback.
    """
    ja = ja.strip()
    if not ja:
        return ja

    # 1. Static map — handles the most common colors perfectly
    mapped = _static_map_color(ja)
    if mapped != ja:
        return mapped

    # 2. Already ASCII/English
    if not _has_japanese(ja):
        return ja

    # 3. Romaji fallback — at least human-readable and consistent
    return _katakana_to_romaji(ja)
