"""Smoke-test réseau réel (opt-in) : confirme que l'API VeryChic répond toujours.

Exécution : `pytest -m network`. Exclu de la CI par défaut (addopts).
Faible volume (le rate-limiter du client espace les requêtes).
"""
import pytest

from verychic_mcp.api import list_deals, offer_details
from verychic_mcp.discovery import get_channel_version
from verychic_mcp.http_client import VeryChicClient

pytestmark = pytest.mark.network


def test_list_deals_live_returns_offers():
    offers = list_deals(VeryChicClient(), limit=5)
    assert offers, "aucune offre renvoyée par l'API live"
    first = offers[0]
    assert first.external_id is not None
    assert first.name


def test_offer_details_live_has_availabilities():
    client = VeryChicClient()
    offer = list_deals(client, limit=1)[0]
    cv = get_channel_version(client)
    details = offer_details(client, offer.source, offer.external_id, channel_version=cv)
    assert details.offer.external_id == offer.external_id
    # la dispo peut être vide selon l'offre, mais l'appel doit aboutir et parser
    assert isinstance(details.availabilities, list)
