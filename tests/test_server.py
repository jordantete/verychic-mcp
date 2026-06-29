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


def test_tools_declare_readonly_annotations():
    # Glama TDQS rewards explicit behavioural annotations. All three tools are
    # read-only and hit a live external API: readOnlyHint + openWorldHint, plus a
    # human-friendly title, must be advertised.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    tools = {t.name: t for t in asyncio.run(srv.list_tools())}
    for name, t in tools.items():
        ann = t.annotations
        assert ann is not None, name
        assert ann.readOnlyHint is True, name
        assert ann.openWorldHint is True, name
        assert ann.title, name


def test_tools_declare_output_schema():
    # Glama explicitly penalises the missing output schema. Each tool must expose one.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    tools = {t.name: t for t in asyncio.run(srv.list_tools())}
    for name, t in tools.items():
        assert t.outputSchema is not None, name


def test_list_deals_structured_result_matches_schema():
    # The typed return must produce structured content whose shape matches what the
    # tool actually returns (offer fields + the computed offer_url).
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    _content, structured = asyncio.run(srv.call_tool("verychic_list_deals", {"limit": 5}))
    assert structured is not None
    assert "result" in structured and structured["result"], "expected at least one offer"
    first = structured["result"][0]
    assert "source" in first and "external_id" in first
    assert "offer_url" in first


def test_offer_details_structured_result_matches_schema():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    _content, structured = asyncio.run(srv.call_tool(
        "verychic_offer_details", {"source": "ORCHESTRA", "external_id": 44983}))
    assert structured is not None
    assert "offer" in structured and "offer_url" in structured["offer"]
    assert "availabilities" in structured
    assert "availabilities_supported" in structured
    assert "cheapest_price" in structured


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
    assert "__VIDEO_URL__" not in html
    assert "__POSTER_URL__" not in html
    assert PYPI_URL in html


def test_landing_video_and_poster_are_app_served():
    # The demo video must be served by the app (correct Content-Type), not from
    # GitHub raw (which serves .mp4 as application/octet-stream + nosniff).
    from verychic_mcp.landing import POSTER_URL, VIDEO_URL, render_landing
    assert VIDEO_URL == "/assets/connect-claude-desktop.mp4"
    assert POSTER_URL == "/assets/connect-claude-desktop-poster.png"
    html = render_landing("https://example.test/mcp")
    assert 'src="/assets/connect-claude-desktop.mp4"' in html
    assert 'poster="/assets/connect-claude-desktop-poster.png"' in html


def test_assets_route_serves_video_with_video_mime():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    with TestClient(srv.streamable_http_app()) as c:
        r = c.get("/assets/connect-claude-desktop.mp4")
    assert r.status_code == 200
    assert r.headers["content-type"] == "video/mp4"
    assert int(r.headers["content-length"]) > 0


def test_assets_route_serves_poster_as_png():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    with TestClient(srv.streamable_http_app()) as c:
        r = c.get("/assets/connect-claude-desktop-poster.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_assets_route_404_for_unknown_name():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    with TestClient(srv.streamable_http_app()) as c:
        r = c.get("/assets/does-not-exist.mp4")
    assert r.status_code == 404


def test_assets_route_404_for_path_traversal():
    # Only whitelisted basenames are served; traversal must never reach the repo.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    with TestClient(srv.streamable_http_app()) as c:
        r = c.get("/assets/..%2f..%2fpyproject.toml")
    assert r.status_code == 404


def test_build_server_disables_dns_rebinding_protection():
    # Remote deployment behind a proxy (Fly): the SDK's localhost-only protection
    # would reject the public Host ("Invalid Host header"). It must stay disabled.
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    assert srv.settings.transport_security is not None
    assert srv.settings.transport_security.enable_dns_rebinding_protection is False


def test_search_offers_structured_result_has_new_fields():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    _content, structured = asyncio.run(srv.call_tool("verychic_search_offers", {"limit": 5}))
    assert structured is not None and structured["result"]
    first = structured["result"][0]
    for key in ("stars", "price_label", "price_with_flights", "flights_included", "rating"):
        assert key in first, key


def test_search_offers_accepts_sort_and_filter_params():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    _content, structured = asyncio.run(srv.call_tool(
        "verychic_search_offers", {"sort_by": "discount", "min_discount": 50}))
    assert structured is not None
    assert structured["result"], "expected at least one offer with discount >= 50 in the fixture"
    discounts = [o["discount"] for o in structured["result"]]
    assert discounts == sorted(discounts, reverse=True)
    assert all(d >= 50 for d in discounts)


def test_search_offers_geo_params_return_distance_km():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    _content, structured = asyncio.run(srv.call_tool(
        "verychic_search_offers",
        {"near_lat": 48.8566, "near_lng": 2.3522, "sort_by": "distance", "limit": 5}))
    assert structured is not None and structured["result"]
    first = structured["result"][0]
    assert "distance_km" in first
    # nearest-first: the French offer (id 25122, ~112 km) leads
    assert first["external_id"] == 25122
    assert first["distance_km"] is not None


def test_search_offers_distance_km_null_without_center():
    srv = build_server(client=RouterClient(), channel_version="26.06.18.00")
    _content, structured = asyncio.run(srv.call_tool("verychic_search_offers", {"limit": 1}))
    assert structured is not None and structured["result"]
    assert structured["result"][0]["distance_km"] is None
