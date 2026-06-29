"""Curated mapping from VeryChic's cryptic `thematics` codes to readable themes.

The live catalogue tags each offer with opaque `thematics` codes (e.g. "PISCINE",
"SOLEIL5H", "R1000"). Most are internal price buckets, calendar campaigns, or sales
channels, and several duplicate existing filters (discount/stars/flights). Only codes
that decode with certainty and aren't already covered become user-facing themes.

The mapping is deliberately conservative and lives in this one file so it is easy to
extend as codes are confirmed. Unknown/volatile codes are silently ignored.
"""
from __future__ import annotations

# theme key -> the raw `thematics` codes that mean it. Single source of truth.
THEME_TO_CODES: dict[str, frozenset[str]] = {
    "pool": frozenset({"PISCINE"}),
    "sun": frozenset({"SOLEIL5H", "SOLHIV"}),
    "last_minute": frozenset({"TONIGHTISH"}),
    "romantic": frozenset({"LOVE"}),
    "island": frozenset({
        "ILES", "ILESMEDIT", "ILESESP", "ILESITA", "ILESIND", "ILESITALIENNES", "TO_ISLANDS",
    }),
    "nature": frozenset({"NATURE", "IMNATURE"}),
    "city_break": frozenset({"CITYBREAKFRANCE", "CITYBREAKEUROPE", "CITYBREAKSMONDE"}),
    "luxury": frozenset({"PRESTIGE", "ALLLUXE"}),
    "spa": frozenset({"SPA"}),
    "rooftop": frozenset({"ROOFTOP"}),
    "adults_only": frozenset({"ADULTS"}),
    "cruise": frozenset({"CROISIERES"}),
    "villa": frozenset({"VILLAS"}),
    "mountain": frozenset({"1MONTAGNE"}),
}

# Exposed enum for the server tool's `theme` parameter (keep in sync via test_server).
THEME_NAMES: tuple[str, ...] = tuple(sorted(THEME_TO_CODES))

# Reverse index, built once: raw code -> theme key.
_CODE_TO_THEME: dict[str, str] = {
    code: theme for theme, codes in THEME_TO_CODES.items() for code in codes
}


def decode_themes(codes: list[str] | None) -> list[str]:
    """Map raw `thematics` codes to curated theme labels.

    Sorted, de-duplicated; unknown codes are dropped; None/empty -> []. Never raises.
    Callers pass the offer's raw `thematics` list (or None).
    """
    if not codes:
        return []
    found = {_CODE_TO_THEME[c] for c in codes if c in _CODE_TO_THEME}
    return sorted(found)
