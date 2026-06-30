import json
from datetime import date
from pathlib import Path

import pytest

from verychic_mcp.api import default_months, offer_details, search_offers
from verychic_mcp.errors import NotFound, UpstreamError, VeryChicError

FIX = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class RouterClient:
    """Fake client: routes each URL to the right fixture, logs the params.

    ``raise_on`` is an optional dict mapping a URL substring to an exception
    to raise instead of returning the matching fixture.
    """
    def __init__(self, raise_on=None):
        self.calls = []
        self._raise_on = raise_on or {}

    def get_json(self, url, params=None):
        self.calls.append((url, params))
        for substring, exc in self._raise_on.items():
            if substring in url:
                raise exc
        if "/products.json" in url:
            return _load("products_sample.json")
        if "/vacation-package/" in url:
            return _load("hotel_sample.json")
        if "/hotel/" in url:
            return _load("hotel_sample.json")
        if "/preview.json" in url:
            return _load("preview_sample.json")
        if "checkin-availabilities" in url:
            return _load("checkin_availabilities_sample.json")
        raise AssertionError(f"Unexpected URL: {url}")


def test_search_limits_results():
    offers = search_offers(RouterClient(), limit=2)
    assert len(offers) == 2
    assert offers[0].external_id == 301375  # catalogue order, first N


def test_search_filters_by_country():
    offers = search_offers(RouterClient(), country="Monténégro")
    assert offers and all(o.country == "Monténégro" for o in offers)


def test_search_filters_by_max_price():
    offers = search_offers(RouterClient(), max_price=520)
    assert offers and all(o.price is not None and o.price <= 520 for o in offers)


def test_search_filters_by_destination_substring():
    offers = search_offers(RouterClient(), destination="herceg")
    assert offers and any("Herceg" in (o.destination or "") for o in offers)


def test_offer_details_calls_three_routes_and_combines():
    c = RouterClient()
    details = offer_details(c, "ORCHESTRA", 44983, channel_version="26.06.18.00")
    assert details.offer.external_id == 44983
    assert details.cheapest_price == 169
    urls = " ".join(u for u, _ in c.calls)
    assert "/hotel/ORCHESTRA/44983.json" in urls
    assert "/product/ORCHESTRA/44983/fr/preview.json" in urls
    assert "/product/ORCHESTRA/44983/checkin-availabilities.json" in urls


def test_default_months_format():
    months = default_months(3, today=date(2026, 11, 15))
    assert months == ["11/2026", "12/2026", "01/2027"]


def test_offer_details_package_uses_vacation_package_route():
    """ORCHESTRA_TO must use /vacation-package/, not /hotel/."""
    c = RouterClient(raise_on={"/hotel/ORCHESTRA_TO/": NotFound()})
    details = offer_details(c, "ORCHESTRA_TO", 44983, channel_version="26.06.18.00")
    urls = [u for u, _ in c.calls]
    assert any("/vacation-package/ORCHESTRA_TO/44983.json" in u for u in urls)
    assert not any("/hotel/ORCHESTRA_TO/" in u for u in urls)
    assert details.offer.external_id == 44983


def test_offer_details_availabilities_best_effort_on_error():
    """A failing checkin-availabilities must not break offer_details."""
    c = RouterClient(raise_on={"checkin-availabilities": UpstreamError()})
    details = offer_details(c, "ORCHESTRA", 44983, channel_version="26.06.18.00")
    assert details.availabilities == []


def test_offer_details_package_marks_availabilities_unsupported():
    """ORCHESTRA_TO packages don't expose date availability: flag it explicitly."""
    c = RouterClient(raise_on={"checkin-availabilities": NotFound()})
    details = offer_details(c, "ORCHESTRA_TO", 44983, channel_version="26.06.18.00")
    assert details.availabilities_supported is False
    assert details.availabilities == []


def test_offer_details_hotel_marks_availabilities_supported():
    """ORCHESTRA hotels expose date availability: flagged as supported."""
    c = RouterClient()
    details = offer_details(c, "ORCHESTRA", 44983, channel_version="26.06.18.00")
    assert details.availabilities_supported is True


def test_search_filters_by_min_discount():
    offers = search_offers(RouterClient(), min_discount=50)
    # Only Sofitel (61.0) clears the bar; None-discount offers are excluded.
    assert offers and all(o.discount is not None and o.discount >= 50 for o in offers)
    assert all(o.discount != 47.0 for o in offers)


def test_search_filters_by_min_stars():
    assert search_offers(RouterClient(), min_stars=5) == []        # none are 5*
    assert len(search_offers(RouterClient(), min_stars=4)) == 3    # all are 4*


def test_search_filters_by_flights_included():
    offers = search_offers(RouterClient(), flights_included=True)
    assert offers and all(o.flights_included is True for o in offers)
    assert len(offers) == 1  # only the OPTIONAL_FLIGHT offer


def test_search_sort_by_discount_desc_with_none_last():
    offers = search_offers(RouterClient(), sort_by="discount")
    discounts = [o.discount for o in offers]
    assert discounts == [61.0, 47.0, None]  # descending, None placed last


def test_search_sort_by_price_asc():
    offers = search_offers(RouterClient(), sort_by="price")
    prices = [o.price for o in offers]
    assert prices == sorted(prices)


def test_search_default_sort_preserves_catalogue_order():
    offers = search_offers(RouterClient())
    # Independent ground truth from the fixture: catalogue order is preserved
    # when sort_by is None.
    assert [o.external_id for o in offers] == [301375, 36509, 25122]


# Center used by the geo tests: Paris.
PARIS = (48.8566, 2.3522)


def test_search_computes_distance_km_when_center_given():
    offers = search_offers(RouterClient(), near_lat=PARIS[0], near_lng=PARIS[1])
    by_id = {o.external_id: o for o in offers}
    assert abs(by_id[25122].distance_km - 111.6) < 2.0  # Empreinte, France


def test_search_distance_km_none_without_center():
    offers = search_offers(RouterClient())
    assert all(o.distance_km is None for o in offers)


def test_search_radius_km_filters_out_far_offers():
    offers = search_offers(RouterClient(), near_lat=PARIS[0], near_lng=PARIS[1], radius_km=500)
    # Only the French offer (~112 km) is within 500 km; Montenegro/NYC are excluded.
    assert [o.external_id for o in offers] == [25122]


def test_search_sort_by_distance_orders_nearest_first():
    offers = search_offers(RouterClient(), near_lat=PARIS[0], near_lng=PARIS[1], sort_by="distance")
    assert [o.external_id for o in offers] == [25122, 301375, 36509]


def test_search_one_coordinate_without_the_other_raises():
    with pytest.raises(VeryChicError):
        search_offers(RouterClient(), near_lat=PARIS[0])
    with pytest.raises(VeryChicError):
        search_offers(RouterClient(), near_lng=PARIS[1])


def test_search_radius_or_distance_sort_without_center_raises():
    with pytest.raises(VeryChicError):
        search_offers(RouterClient(), radius_km=500)
    with pytest.raises(VeryChicError):
        search_offers(RouterClient(), sort_by="distance")


def test_search_offers_theme_keeps_only_matching():
    # Offer 301375 has themes ['pool', 'sun']; others do not have 'pool'.
    res = search_offers(RouterClient(), theme="pool")
    assert [o.external_id for o in res] == [301375]


def test_search_offers_theme_no_match_returns_empty():
    assert search_offers(RouterClient(), theme="spa") == []


def test_search_offers_theme_combines_with_other_filter():
    # 25122 has theme 'last_minute' but is in France, not Italie — yields nothing.
    assert search_offers(RouterClient(), theme="last_minute", country="Italie") == []
