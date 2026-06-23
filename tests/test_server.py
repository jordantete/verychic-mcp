import asyncio
import json
from pathlib import Path

from starlette.testclient import TestClient

from verychic_mcp.server import LOGO_URL, build_server, resolve_transport

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


def test_build_server_declares_icon_and_website():
    # The custom remote connector shows a generic globe unless the server declares
    # an icon in serverInfo. We expose the project logo (raw GitHub URL) + website.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    assert srv.website_url == "https://github.com/jordantete/verychic-mcp"
    assert srv.icons, "server should declare at least one icon"
    icon = srv.icons[0]
    assert icon.src.endswith("assets/logo.png")
    assert icon.mimeType == "image/png"


def test_favicon_route_redirects_to_logo():
    # Remote connectors take their icon from the domain favicon, not serverInfo,
    # so we redirect /favicon.ico to the public logo.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    with TestClient(srv.streamable_http_app()) as c:
        r = c.get("/favicon.ico", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == LOGO_URL


def test_root_page_links_icon():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    with TestClient(srv.streamable_http_app()) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert LOGO_URL in r.text
    # Landing content: the 3 tools and the live endpoint (built from the Host header).
    assert "verychic_list_deals" in r.text
    assert "verychic_offer_details" in r.text
    assert "https://testserver/mcp" in r.text


def test_safe_host_rejects_injection():
    from verychic_mcp.server import _safe_host
    # A malicious Host header must never be reflected into the page.
    assert _safe_host('evil"><script>alert(1)</script>') == "verychic-mcp.fly.dev"
    assert _safe_host(None) == "verychic-mcp.fly.dev"
    assert _safe_host("") == "verychic-mcp.fly.dev"
    # Legitimate hosts (with port) pass through unchanged.
    assert _safe_host("verychic-mcp.fly.dev") == "verychic-mcp.fly.dev"
    assert _safe_host("localhost:8000") == "localhost:8000"


def test_root_page_does_not_reflect_malicious_host():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    with TestClient(srv.streamable_http_app()) as c:
        r = c.get("/", headers={"host": "a.example/../<svg onload=alert(1)>"})
    assert r.status_code == 200
    assert "<svg onload" not in r.text
    assert "https://verychic-mcp.fly.dev/mcp" in r.text


def test_render_landing_injects_endpoint():
    from verychic_mcp.landing import PYPI_URL, render_landing
    html = render_landing("https://example.test/mcp")
    assert "https://example.test/mcp" in html
    assert "__ENDPOINT__" not in html  # all tokens replaced
    assert "__LOGO_URL__" not in html
    assert PYPI_URL in html


def test_build_server_disables_dns_rebinding_protection():
    # Remote deployment behind a proxy (Fly): the SDK's localhost-only protection
    # would reject the public Host ("Invalid Host header"). It must stay disabled.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    assert srv.settings.transport_security is not None
    assert srv.settings.transport_security.enable_dns_rebinding_protection is False
