"""MCP server (FastMCP) exposing the 3 VeryChic tools, dual transport."""
from __future__ import annotations

import argparse
import re
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import Icon
from starlette.responses import HTMLResponse, RedirectResponse

from . import api
from .discovery import get_channel_version
from .http_client import VeryChicClient
from .landing import LOGO_URL, WEBSITE_URL, render_landing

# Hostname chars + optional port only. Rejecting anything else keeps the (attacker-
# controlled) Host header out of the landing HTML — no reflected XSS possible.
_HOST_RE = re.compile(r"^[A-Za-z0-9.\-:]+$")
_DEFAULT_HOST = "verychic-mcp.fly.dev"


def _safe_host(raw: str | None) -> str:
    return raw if raw and _HOST_RE.match(raw) else _DEFAULT_HOST


def resolve_transport(argv: list[str]) -> tuple[str, str, int]:
    parser = argparse.ArgumentParser(prog="verychic-mcp")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    ns = parser.parse_args(argv)
    return ns.transport, ns.host, ns.port


def _offer_dict(offer) -> dict:
    d = asdict(offer)
    d["offer_url"] = offer.offer_url
    return d


def build_server(*, client=None, channel_version=None) -> FastMCP:
    client = client if client is not None else VeryChicClient()
    if channel_version is None:
        channel_version = get_channel_version(client)
    # Remote HTTP transport: the server is public/anonymous and runs behind a proxy
    # (Fly, etc.) that presents a public Host. The SDK's DNS-rebinding protection only
    # allows localhost by default and would reject that Host ("Invalid Host header").
    # We disable it explicitly: no secret nor localhost binding to protect here.
    # Declare a website and an icon in serverInfo so clients (e.g. a Claude Desktop
    # custom connector) can show the project logo instead of the generic placeholder.
    mcp = FastMCP(
        "verychic",
        website_url=WEBSITE_URL,
        icons=[Icon(src=LOGO_URL, mimeType="image/png", sizes=["512x512"])],
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    # The HTTP origin also serves a favicon (redirect to the public logo) and a
    # landing page at "/", so visiting the deployment URL shows a real page.
    @mcp.custom_route("/favicon.ico", methods=["GET"])
    async def favicon(request):  # noqa: ANN001, ANN202
        return RedirectResponse(LOGO_URL)

    @mcp.custom_route("/", methods=["GET"])
    async def index(request):  # noqa: ANN001, ANN202
        host = _safe_host(request.headers.get("host"))
        return HTMLResponse(render_landing(f"https://{host}/mcp"))

    @mcp.tool()
    def verychic_list_deals(limit: int = 20) -> list[dict]:
        """List current VeryChic offers (20 by default)."""
        return [_offer_dict(o) for o in api.list_deals(client, limit=limit)]

    @mcp.tool()
    def verychic_search_offers(destination: str | None = None, country: str | None = None,
                               max_price: float | None = None, limit: int = 20) -> list[dict]:
        """Search/filter offers by destination (substring), country, and/or max price."""
        offers = api.search_offers(client, destination=destination, country=country,
                                   max_price=max_price, limit=limit)
        return [_offer_dict(o) for o in offers]

    @mcp.tool()
    def verychic_offer_details(source: str, external_id: int) -> dict:
        """Offer details (advantages, gallery) plus availability/prices by date."""
        details = api.offer_details(client, source, external_id, channel_version=channel_version)
        out = asdict(details)
        out["offer"]["offer_url"] = details.offer.offer_url
        out["cheapest_price"] = details.cheapest_price
        return out

    return mcp


def main(argv: list[str] | None = None) -> int:
    import sys
    transport, host, port = resolve_transport(argv if argv is not None else sys.argv[1:])
    mcp = build_server()
    if transport == "streamable-http":
        mcp.settings.host = host
        mcp.settings.port = port
    mcp.run(transport=transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
