"""MCP server (FastMCP) exposing the 3 VeryChic tools, dual transport."""
from __future__ import annotations

import argparse
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import Icon
from starlette.responses import HTMLResponse, RedirectResponse

from . import api
from .discovery import get_channel_version
from .http_client import VeryChicClient

# Public project logo (already served from the repo, see README header).
LOGO_URL = "https://raw.githubusercontent.com/jordantete/verychic-mcp/main/assets/logo.png"
WEBSITE_URL = "https://github.com/jordantete/verychic-mcp"


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

    # Remote connectors derive their icon from the origin's favicon, not serverInfo.
    # Serve a favicon (redirect to the public logo) and a small landing page that
    # links it, so the logo shows up instead of the generic globe.
    @mcp.custom_route("/favicon.ico", methods=["GET"])
    async def favicon(request):  # noqa: ANN001, ANN202
        return RedirectResponse(LOGO_URL)

    @mcp.custom_route("/", methods=["GET"])
    async def index(request):  # noqa: ANN001, ANN202
        return HTMLResponse(
            f'<!doctype html><html><head><meta charset="utf-8">'
            f'<title>VeryChic MCP</title>'
            f'<link rel="icon" type="image/png" href="{LOGO_URL}">'
            f'</head><body><h1>VeryChic MCP</h1>'
            f'<p>Unofficial, read-only MCP server for VeryChic hotel offers. '
            f'MCP endpoint: <code>/mcp</code>. '
            f'<a href="{WEBSITE_URL}">Project on GitHub</a>.</p></body></html>'
        )

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
