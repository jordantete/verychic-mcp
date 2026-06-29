import json
from pathlib import Path

from verychic_mcp.models import Availability, Offer, OfferDetails
from verychic_mcp.parsers import (
    parse_availabilities,
    parse_offer,
    parse_offer_details,
    parse_offers,
)

FIX = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_parse_offers_from_products_fixture():
    offers = parse_offers(_load("products_sample.json"))
    assert len(offers) == 3
    first = offers[0]
    assert isinstance(first, Offer)
    assert first.source == "ORCHESTRA_TO"
    assert first.external_id == 301375
    assert first.name.startswith("Kappa Club Iberostar")
    assert first.country == "Monténégro"
    assert first.price == 515
    assert first.currency == "EUR"
    assert first.url_name == "montenegro-herceg-novi-hotel-kappa-club-iberostar-herceg-novi-4-etoiles"  # noqa: E501


def test_offer_url_built_from_id_and_slug():
    first = parse_offers(_load("products_sample.json"))[0]
    assert first.offer_url == (
        "https://www.verychic.fr/p/301375/"
        "montenegro-herceg-novi-hotel-kappa-club-iberostar-herceg-novi-4-etoiles"
    )


def test_offer_url_none_without_slug():
    assert parse_offer({"source": "X", "externalId": 1, "name": "n"}).offer_url is None


def test_parse_availabilities_from_fixture():
    avails = parse_availabilities(_load("checkin_availabilities_sample.json"))
    assert len(avails) == 5
    assert isinstance(avails[0], Availability)
    assert avails[0].date == "20/06/2026"
    assert avails[0].price == 169
    assert avails[0].currency == "EUR"
    assert avails[0].nights == 1


def test_parse_offer_details_combines_sources():
    details = parse_offer_details(
        _load("hotel_sample.json"),
        _load("preview_sample.json"),
        _load("checkin_availabilities_sample.json"),
    )
    assert isinstance(details, OfferDetails)
    assert details.offer.external_id == 44983
    assert isinstance(details.advantages, list) and details.advantages
    assert isinstance(details.gallery, list)
    assert len(details.availabilities) == 5
    assert details.cheapest_price == 169  # min des prix de dispo


def test_offer_details_availabilities_supported_defaults_true():
    details = parse_offer_details(
        _load("hotel_sample.json"),
        _load("preview_sample.json"),
        _load("checkin_availabilities_sample.json"),
    )
    assert details.availabilities_supported is True


def test_offer_details_availabilities_supported_can_be_false():
    details = parse_offer_details(
        _load("hotel_sample.json"),
        _load("preview_sample.json"),
        [],
        availabilities_supported=False,
    )
    assert details.availabilities_supported is False


def test_parse_offer_extracts_stars_from_name():
    offers = parse_offers(_load("products_sample.json"))
    assert offers[0].stars == 4  # name ends with "****"


def test_parse_stars_falls_back_to_url_name():
    from verychic_mcp.parsers import parse_stars
    assert parse_stars("Hotel without rating", "ville-hotel-x-4-etoiles") == 4


def test_parse_stars_none_when_absent():
    from verychic_mcp.parsers import parse_stars
    assert parse_stars("Plain hotel name", None) is None


def test_parse_offer_builds_price_label():
    offers = parse_offers(_load("products_sample.json"))
    # pricePreLabel + pricePostLabel recombined
    assert offers[0].price_label == "à partir de par pers. pour 3 nuits"
    assert offers[1].price_label == "à partir de par chambre"


def test_parse_offer_price_with_flights_zero_becomes_none():
    offers = parse_offers(_load("products_sample.json"))
    assert offers[0].price_with_flights == 515   # non-zero kept
    assert offers[1].price_with_flights is None   # 0 -> None
    assert offers[2].price_with_flights is None   # missing -> None


def test_parse_offer_flights_included_from_transportation():
    offers = parse_offers(_load("products_sample.json"))
    assert offers[0].flights_included is True    # OPTIONAL_FLIGHT
    assert offers[1].flights_included is False   # NONE


def test_parse_offer_rating_from_opinions():
    offers = parse_offers(_load("products_sample.json"))
    assert offers[0].rating is None  # opinions.generalGrade is null in catalogue
