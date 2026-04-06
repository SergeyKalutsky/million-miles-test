"""
Model name resolver: Japanese katakana → English car model name.

Strategy:
  1. Check static MODEL_MAP first (instant, exact).
  2. Convert katakana to romaji via pykakasi.
  3. Fuzzy-match the romaji against a comprehensive English model list
     using rapidfuzz. Accept matches above a confidence threshold.
  4. Fall back to the original string if confidence is too low.

This handles names like:
  グランドチェロキー  → "Grand Cherokee"
  ディフェンダー      → "Defender"
  レンジローバー      → "Range Rover"
  ムスタング          → "Mustang"
"""

from __future__ import annotations

import logging
import re
import unicodedata

from scraper.normalizers import MODEL_MAP

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Comprehensive English model list used for fuzzy matching
# Romaji of each will be compared against romaji of the unknown input.
# Add more freely — this is just a lookup corpus, not persisted anywhere.
# ---------------------------------------------------------------------------

KNOWN_MODELS: list[str] = [
    # Toyota
    "Prius", "Crown", "Camry", "Corolla", "Land Cruiser", "Hiace", "Alphard",
    "Vellfire", "Harrier", "Voxy", "Sienta", "Yaris", "Aqua", "Noah",
    "Estima", "Celsior", "Supra", "86", "GR86", "GR Yaris", "C-HR",
    "RAV4", "Fortuner", "Hilux", "Avensis", "Auris", "Verso",
    # Honda
    "Fit", "Civic", "Accord", "Step WGN", "Freed", "Vezel", "N-BOX",
    "Odyssey", "Legend", "Insight", "CR-V", "HR-V", "Jazz", "Life",
    "Zest", "Element", "Pilot", "Ridgeline",
    # Nissan
    "Skyline", "Fairlady Z", "Note", "Serena", "X-Trail", "Juke",
    "Caravan", "Elgrand", "Leaf", "Ariya", "Kicks", "Terra",
    "Patrol", "Navara", "Titan", "Maxima", "Altima", "Sentra",
    # Subaru
    "Impreza", "Legacy", "Forester", "Outback", "Levorg", "BRZ",
    "Crosstrek", "Ascent", "WRX", "Tribeca",
    # Mazda
    "Demio", "Atenza", "Axela", "CX-5", "CX-3", "CX-8", "CX-9",
    "Roadster", "MX-5", "RX-7", "RX-8", "Tribute",
    # Mitsubishi
    "Outlander", "Eclipse Cross", "Pajero", "Delica", "ASX",
    "Galant", "Lancer", "Colt", "i-MiEV",
    # Suzuki
    "Jimny", "Swift", "Solio", "Hustler", "Alto", "Wagon R",
    "Vitara", "SX4", "Ignis", "Baleno",
    # Daihatsu
    "Mira", "Tanto", "Move", "Copen", "Rocky", "Taft", "Cast",
    # Mercedes-Benz
    "A-Class", "B-Class", "C-Class", "E-Class", "S-Class",
    "GLA", "GLB", "GLC", "GLE", "GLS", "G-Class", "AMG GT",
    "CLA", "CLS", "SL", "SLC", "Maybach", "EQS", "EQE",
    # BMW
    "1 Series", "2 Series", "3 Series", "4 Series", "5 Series",
    "6 Series", "7 Series", "8 Series",
    "X1", "X2", "X3", "X4", "X5", "X6", "X7",
    "Z4", "M3", "M5", "Gran Coupe", "Gran Turismo", "i3", "i4", "iX",
    # Audi
    "A1", "A3", "A4", "A5", "A6", "A7", "A8",
    "Q2", "Q3", "Q5", "Q7", "Q8",
    "TT", "R8", "e-tron", "Quattro",
    # Volkswagen
    "Golf", "Polo", "Passat", "Tiguan", "Touareg", "T-Roc",
    "Arteon", "ID.3", "ID.4", "Beetle", "Scirocco",
    # Porsche
    "Cayenne", "Macan", "Panamera", "Taycan", "Boxster", "Cayman",
    "911", "918",
    # Land Rover / Range Rover
    "Defender", "Discovery", "Freelander", "Range Rover",
    "Range Rover Sport", "Range Rover Evoque", "Range Rover Velar",
    # Jeep
    "Grand Cherokee", "Cherokee", "Wrangler", "Renegade",
    "Compass", "Gladiator", "Commander",
    # Ford
    "Mustang", "Explorer", "Escape", "Edge", "Bronco",
    "F-150", "Focus", "Fiesta", "Mondeo", "Kuga", "Puma",
    # Chevrolet / GM
    "Corvette", "Camaro", "Tahoe", "Suburban", "Silverado",
    "Equinox", "Traverse", "Malibu", "Trailblazer",
    # Cadillac
    "Escalade", "CT5", "CT6", "XT4", "XT5", "XT6",
    # Dodge / Chrysler
    "Challenger", "Charger", "Durango", "Grand Caravan",
    "300", "Pacifica",
    # Alfa Romeo
    "Giulia", "Giulietta", "Stelvio", "MiTo", "Spider", "Brera",
    "Tonale", "4C",
    # Ferrari
    "California", "Portofino", "Roma", "Testarossa",
    "488", "F8", "SF90", "812", "GTC4",
    # Lamborghini
    "Huracán", "Aventador", "Urus", "Gallardo", "Murcielago",
    # Maserati
    "Quattroporte", "Ghibli", "GranCabrio", "GranTurismo",
    "Levante", "Grecale",
    # Rolls-Royce
    "Phantom", "Wraith", "Ghost", "Cullinan", "Dawn", "Spectre",
    # Bentley
    "Continental", "Flying Spur", "Bentayga", "Mulsanne",
    # McLaren
    "720S", "570S", "GT", "Artura",
    # Tesla
    "Model S", "Model 3", "Model X", "Model Y", "Cybertruck",
    # Volvo
    "XC40", "XC60", "XC90", "V60", "V90", "S60", "S90", "EX30",
    # Peugeot / Citroën / Renault
    "208", "308", "508", "2008", "3008", "5008",
    "C3", "C4", "C5", "Berlingo",
    "Clio", "Megane", "Kadjar", "Koleos",
    # Hyundai / Kia
    "Tucson", "Santa Fe", "Sonata", "Elantra", "Ioniq",
    "Stinger", "Sorento", "Sportage", "Carnival",
    # Lincoln / Hummer / other
    "Navigator", "Aviator", "Corsair", "H2", "H3",
]

# Pre-build romaji index at import time
_kks = None
_model_romaji_index: list[tuple[str, str]] = []  # [(romaji, english), ...]


def _get_kks():
    global _kks
    if _kks is None:
        import pykakasi
        _kks = pykakasi.kakasi()
    return _kks


def _to_romaji(text: str) -> str:
    """Convert Japanese (katakana/hiragana) + ASCII text to lowercase romaji."""
    result = _get_kks().convert(text)
    parts = [item["hepburn"] for item in result]
    romaji = " ".join(parts)
    # Collapse multiple spaces, lowercase
    romaji = re.sub(r"\s+", " ", romaji).strip().lower()
    return romaji


def _build_index() -> list[tuple[str, str]]:
    """Build (romaji, english) index from KNOWN_MODELS."""
    index = []
    for model in KNOWN_MODELS:
        romaji = _to_romaji(model)
        index.append((romaji, model))
    return index


def _get_index() -> list[tuple[str, str]]:
    global _model_romaji_index
    if not _model_romaji_index:
        _model_romaji_index = _build_index()
    return _model_romaji_index


def resolve_model(ja: str, threshold: int = 72) -> str:
    """
    Try to map a Japanese model name to English.

    1. Check static MODEL_MAP first (exact match, handles all known models).
    2. Returns ja unchanged if it's already ASCII (already English or a code like "GR86").
    3. Converts katakana→romaji then fuzzy-matches against KNOWN_MODELS.
    4. Returns English match if score >= threshold, else returns ja unchanged.
    """
    ja = ja.strip()

    # 1. Static map — handles all known Japanese model names exactly
    if ja in MODEL_MAP:
        return MODEL_MAP[ja]

    # 2. Already ASCII/English — return as-is
    if all(ord(c) < 128 or c in "-/ " for c in ja):
        return ja

    # Check if it contains any Japanese characters at all
    has_japanese = any(unicodedata.category(c) in ("Lo",) for c in ja)
    if not has_japanese:
        return ja

    try:
        from rapidfuzz import process, fuzz

        input_romaji = _to_romaji(ja)
        index = _get_index()
        romaji_list = [r for r, _ in index]

        # Use token_sort_ratio so word order differences don't hurt
        match = process.extractOne(
            input_romaji,
            romaji_list,
            scorer=fuzz.token_sort_ratio,
        )
        if match and match[1] >= threshold:
            matched_romaji = match[0]
            english = next(eng for rom, eng in index if rom == matched_romaji)
            log.debug("Model '%s' → romaji '%s' → '%s' (score %d)", ja, input_romaji, english, match[1])
            return english

        log.debug("Model '%s' → romaji '%s' → no match (best %s)", ja, input_romaji, match)
    except Exception as exc:
        log.warning("resolve_model failed for '%s': %s", ja, exc)

    return ja
