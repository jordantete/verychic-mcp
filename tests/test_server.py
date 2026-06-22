import asyncio
import json
from pathlib import Path

from verychic_mcp.server import resolve_transport, build_server

FIX = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class RouterClient:
    def get_json(self, url, params=None):
        if "/products.json" in url:
            return _load("products_sample.json")
        if "/hotel/" in url:
            return _load("hotel_sample.json")
        if "/preview.json" in url:
            return _load("preview_sample.json")
        if "checkin-availabilities" in url:
            return _load("checkin_availabilities_sample.json")
        raise AssertionError(url)


def test_resolve_transport_defaults_to_stdio():
    assert resolve_transport([]) == ("stdio", "127.0.0.1", 8000)


def test_resolve_transport_http_with_host_port():
    assert resolve_transport(
        ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "9000"]
    ) == ("streamable-http", "0.0.0.0", 9000)


def test_build_server_registers_three_tools():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    names = {t.name for t in asyncio.run(srv.list_tools())}
    assert names == {"verychic_list_deals", "verychic_search_offers", "verychic_offer_details"}


def test_build_server_disables_dns_rebinding_protection():
    # Déploiement remote derrière un proxy (Fly) : la protection localhost-only du SDK
    # rejetterait le Host public ("Invalid Host header"). Elle doit rester désactivée.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    assert srv.settings.transport_security is not None
    assert srv.settings.transport_security.enable_dns_rebinding_protection is False
