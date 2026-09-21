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


def test_parse_offer_nullifies_implausible_discount():
    # The live catalogue occasionally returns corrupt discounts (e.g. 263%);
    # outside 0-100% it must become None, not surface as a fake "best deal".
    def disc(v):
        return parse_offer({"source": "X", "externalId": 1, "name": "n", "discount": v}).discount
    assert disc(263.0) is None
    assert disc(-5.0) is None
    assert disc(70.0) == 70.0    # plausible value passes through
    assert disc(0.0) == 0.0      # zero discount is valid
    assert disc(100.0) == 100.0  # upper bound inclusive


def test_parse_offer_nullifies_non_positive_price():
    def price(extra):
        return parse_offer({"source": "X", "externalId": 1, "name": "n", **extra}).price
    assert price({"price": -50}) is None
    assert price({"price": 0}) is None
    # falls back to normalizedPrice when the primary price is implausible
    assert price({"price": -50, "normalizedPrice": 200}) == 200
    assert price({"price": 75}) == 75  # plausible price kept


def test_parse_offer_decodes_themes_from_thematics():
    offers = {o.external_id: o for o in parse_offers(_load("products_sample.json"))}
    # 301375 has PISCINE + SOLEIL5H (and many internal codes that are dropped).
    assert offers[301375].themes == ["pool", "sun"]
    # 36509 has CITYBREAKSMONDE + ALLLUXE.
    assert offers[36509].themes == ["city_break", "luxury"]
    # 25122 has TONIGHTISH.
    assert offers[25122].themes == ["last_minute"]


def test_parse_offer_themes_absent_is_empty_list():
    offer = parse_offers({"content": [{"externalId": 1, "name": "X"}]})[0]
    assert offer.themes == []


def test_parse_offer_extracts_opinion_count_and_subgrades():
    # The opinions block is already on the wire (offer_details asks for it); every
    # grade must be exposed, not just generalGrade.
    offer = parse_offer(_load("hotel_sample.json"))
    assert offer.rating == 8.5
    assert offer.opinion_count == 67
    assert offer.rating_location == 8.1
    assert offer.rating_public_area == 9.1
    assert offer.rating_room == 9.2
    assert offer.rating_service == 8.9
    assert offer.rating_food == 9.1


def test_parse_offer_opinions_absent_are_none():
    offer = parse_offer({"source": "X", "externalId": 1, "name": "n"})
    assert offer.opinion_count is None
    assert offer.rating_location is None
    assert offer.rating_room is None


def test_parse_offer_opinion_count_zero_is_kept():
    # 0 reviews is information ("nobody rated this"), not a missing value.
    offers = parse_offers(_load("products_sample.json"))
    assert offers[0].opinion_count == 0


def _avail(date, price, currency="EUR"):
    return Availability(date=date, price=price, currency=currency, nights=1, days=2)


def _months(details):
    return [(m.month, m.min_price, m.currency, m.dates_available)
            for m in details.availabilities_by_month]


def _details_with(avails):
    return OfferDetails(offer=parse_offer({"source": "X", "externalId": 1, "name": "n"}),
                        availabilities=avails)


def test_availabilities_by_month_aggregates_min_price_from_fixture():
    details = parse_offer_details(
        _load("hotel_sample.json"),
        _load("preview_sample.json"),
        _load("checkin_availabilities_sample.json"),
    )
    # the fixture holds 5 dates, all in June 2026, all at 169
    assert _months(details) == [("06/2026", 169, "EUR", 5)]


def test_availabilities_by_month_keeps_the_cheapest_date_of_each_month():
    details = _details_with([_avail("05/10/2026", 240), _avail("12/10/2026", 149),
                             _avail("20/10/2026", 310)])
    assert _months(details) == [("10/2026", 149, "EUR", 3)]


def test_availabilities_by_month_is_chronological_across_a_year_boundary():
    # "MM/YYYY" sorted as text would put 01/2027 first; order must be real time order.
    details = _details_with([_avail("15/01/2027", 200), _avail("03/12/2026", 180),
                             _avail("09/09/2026", 220)])
    assert [m.month for m in details.availabilities_by_month] == [
        "09/2026", "12/2026", "01/2027"]


def test_availabilities_by_month_skips_dates_without_a_price():
    details = _details_with([_avail("05/10/2026", None), _avail("12/10/2026", 149)])
    assert _months(details) == [("10/2026", 149, "EUR", 1)]


def test_availabilities_by_month_drops_a_month_with_no_priced_date():
    details = _details_with([_avail("05/10/2026", None), _avail("12/11/2026", 149)])
    assert [m.month for m in details.availabilities_by_month] == ["11/2026"]


def test_availabilities_by_month_empty_without_availabilities():
    # ORCHESTRA_TO packages expose no date availability at all.
    details = parse_offer_details(
        _load("hotel_sample.json"), _load("preview_sample.json"), [],
        availabilities_supported=False,
    )
    assert details.availabilities_by_month == []


def test_availabilities_by_month_ignores_a_malformed_date():
    # parse_availabilities defaults a missing date to "", which has no month to group on.
    details = _details_with([_avail("", 149), _avail("12/11/2026", 200)])
    assert _months(details) == [("11/2026", 200, "EUR", 1)]
