"""Tests for the curated thematics -> theme mapping."""
from verychic_mcp.themes import THEME_NAMES, THEME_TO_CODES, decode_themes


def test_decode_known_codes_returns_sorted_unique_labels():
    # PISCINE -> pool, SOLEIL5H -> sun; R500/I are internal buckets (dropped).
    assert decode_themes(["PISCINE", "R500", "SOLEIL5H", "I"]) == ["pool", "sun"]


def test_decode_dedupes_when_several_codes_map_to_one_theme():
    # SOLEIL5H and SOLHIV both map to "sun" -> a single label.
    assert decode_themes(["SOLEIL5H", "SOLHIV"]) == ["sun"]


def test_decode_unknown_only_returns_empty():
    assert decode_themes(["R1000", "FR_15AOUT", "WEVC"]) == []


def test_decode_none_and_empty_return_empty():
    assert decode_themes(None) == []
    assert decode_themes([]) == []


def test_theme_names_match_mapping_keys_sorted():
    assert THEME_NAMES == tuple(sorted(THEME_TO_CODES))


def test_every_mapped_code_appears_in_exactly_one_theme():
    seen: dict[str, str] = {}
    for theme, codes in THEME_TO_CODES.items():
        for code in codes:
            assert code not in seen, f"{code} mapped to both {seen.get(code)} and {theme}"
            seen[code] = theme
