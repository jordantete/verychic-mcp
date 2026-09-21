"""Real-network smoke test (opt-in): confirms the VeryChic API still responds.

Run with `pytest -m network`. Excluded from CI by default (addopts).
Low volume (the client's rate-limiter spaces out the requests).
"""
import pytest

from verychic_mcp.api import offer_details, search_offers
from verychic_mcp.discovery import get_channel_version
from verychic_mcp.http_client import VeryChicClient

pytestmark = pytest.mark.network


def test_search_offers_live_returns_offers():
    offers = search_offers(VeryChicClient(), limit=5)
    assert offers, "no offers returned by the live API"
    first = offers[0]
    assert first.external_id is not None
    assert first.name


def test_offer_details_live_has_availabilities():
    client = VeryChicClient()
    offer = search_offers(client, limit=1)[0]
    cv = get_channel_version(client)
    details = offer_details(client, offer.source, offer.external_id, channel_version=cv)
    assert details.offer.external_id == offer.external_id
    # availability may be empty depending on the offer, but the call must succeed and parse
    assert isinstance(details.availabilities, list)
    # the per-month rollup is derived from that same list, so it must agree with it
    by_month = details.availabilities_by_month
    assert [m.month for m in by_month] == sorted(
        (m.month for m in by_month), key=lambda m: (m[-4:], m[:2]))
    if by_month:
        assert details.cheapest_price == min(m.min_price for m in by_month)


def test_offer_details_live_honours_a_custom_month_window():
    """`months` must actually narrow the live query, not be silently ignored."""
    client = VeryChicClient()
    cv = get_channel_version(client)
    hotel = next(o for o in search_offers(client, limit=40) if o.source == "ORCHESTRA")
    default = offer_details(client, hotel.source, hotel.external_id, channel_version=cv)
    if not default.availabilities:
        pytest.skip("offer has no availability in the default window")

    month = default.availabilities[0].date.split("/", 1)[1]  # "DD/MM/YYYY" -> "MM/YYYY"
    narrowed = offer_details(client, hotel.source, hotel.external_id,
                             channel_version=cv, months=[month])
    assert narrowed.availabilities, f"no availability returned for {month}"
    assert all(a.date.endswith(month) for a in narrowed.availabilities)
