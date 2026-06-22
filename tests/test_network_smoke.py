"""Real-network smoke test (opt-in): confirms the VeryChic API still responds.

Run with `pytest -m network`. Excluded from CI by default (addopts).
Low volume (the client's rate-limiter spaces out the requests).
"""
import pytest

from verychic_mcp.api import list_deals, offer_details
from verychic_mcp.discovery import get_channel_version
from verychic_mcp.http_client import VeryChicClient

pytestmark = pytest.mark.network


def test_list_deals_live_returns_offers():
    offers = list_deals(VeryChicClient(), limit=5)
    assert offers, "no offers returned by the live API"
    first = offers[0]
    assert first.external_id is not None
    assert first.name


def test_offer_details_live_has_availabilities():
    client = VeryChicClient()
    offer = list_deals(client, limit=1)[0]
    cv = get_channel_version(client)
    details = offer_details(client, offer.source, offer.external_id, channel_version=cv)
    assert details.offer.external_id == offer.external_id
    # availability may be empty depending on the offer, but the call must succeed and parse
    assert isinstance(details.availabilities, list)
