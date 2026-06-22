import json
from datetime import date
from pathlib import Path

from verychic_mcp.api import default_months, list_deals, offer_details, search_offers
from verychic_mcp.errors import NotFound, UpstreamError

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


def test_list_deals_limits_results():
    offers = list_deals(RouterClient(), limit=2)
    assert len(offers) == 2
    assert offers[0].external_id == 301375


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
