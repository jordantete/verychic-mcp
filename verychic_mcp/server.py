"""MCP server (FastMCP) exposing the 3 VeryChic tools, dual transport."""
from __future__ import annotations

import argparse
import re
from dataclasses import asdict
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import Icon
from pydantic import Field
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
    def verychic_list_deals(
        limit: Annotated[int, Field(
            description="Maximum number of offers to return (default 20). Caps the result "
            "size only; there is no pagination or cursor, so this always returns the first "
            "N offers of the live catalogue.",
        )] = 20,
    ) -> list[dict]:
        """Browse the VeryChic flash-sale hotel offers available right now.

        When to use: to discover the current catalogue without any filter. To narrow by
        destination, country, or price use `verychic_search_offers` instead; to get the
        full detail and per-date prices of one offer use `verychic_offer_details`.

        Behaviour: read-only and anonymous (no account or credentials); rate-limited to
        about 1 request per second. Returns the first `limit` offers in catalogue order
        (no pagination). Prices are in EUR and text is in French. "Current" means live
        offers at call time; the catalogue changes over time.

        Returns a list of offer objects, each with: `source` and `external_id` (the pair
        that identifies an offer for `verychic_offer_details`), `name`, `destination`,
        `country`, `price` and `currency`, `discount`, `short_desc`, `offer_end_date`,
        `latitude`/`longitude`, `image`, `advantages`, and `offer_url` (public web page).
        """
        return [_offer_dict(o) for o in api.list_deals(client, limit=limit)]

    @mcp.tool()
    def verychic_search_offers(
        destination: Annotated[str | None, Field(
            description="Case-insensitive substring matched against each offer's "
            "destination AND name (e.g. 'paris', 'maldives', 'crete'). Omit to not "
            "filter by destination.",
        )] = None,
        country: Annotated[str | None, Field(
            description="Exact country name, case-insensitive, as spelled in the (French) "
            "catalogue, e.g. 'France', 'Italie', 'Grece'. Omit to not filter by country.",
        )] = None,
        max_price: Annotated[float | None, Field(
            description="Inclusive upper bound on the offer price, in EUR. Offers with no "
            "price are excluded when this is set. Omit for no price cap.",
        )] = None,
        limit: Annotated[int, Field(
            description="Maximum number of matching offers to return (default 20), applied "
            "after filtering. No pagination.",
        )] = 20,
    ) -> list[dict]:
        """Search and filter the current VeryChic offers by destination, country, and/or price.

        When to use: when you already know roughly what the user wants (a place, a country,
        a budget). To simply list everything on offer use `verychic_list_deals`; to inspect
        one specific offer in depth use `verychic_offer_details`. All filters are optional
        and combine with AND; calling with no filter is equivalent to `verychic_list_deals`.

        Behaviour: read-only and anonymous; rate-limited to about 1 request per second.
        Filtering is done client-side over the live catalogue: `destination` is a
        case-insensitive substring (matched on destination or name), `country` is an exact
        case-insensitive match, `max_price` is an inclusive EUR ceiling. Prices are in EUR
        and text is in French. Returns the first `limit` matches.

        Returns a list of offer objects with the same fields as `verychic_list_deals`
        (including `source` + `external_id` for use with `verychic_offer_details`). An
        empty list means no offer matched the filters.
        """
        offers = api.search_offers(client, destination=destination, country=country,
                                   max_price=max_price, limit=limit)
        return [_offer_dict(o) for o in offers]

    @mcp.tool()
    def verychic_offer_details(
        source: Annotated[str, Field(
            description="The offer's source type, copied verbatim from the `source` field "
            "of a `verychic_list_deals`/`verychic_search_offers` result. One of "
            "'ORCHESTRA' (a single hotel) or 'ORCHESTRA_TO' (a tour-operator package). "
            "Packages have no per-date availability.",
        )],
        external_id: Annotated[int, Field(
            description="The offer's numeric `external_id`, copied from a "
            "`verychic_list_deals`/`verychic_search_offers` result. Identifies the offer "
            "together with `source`.",
        )],
    ) -> dict:
        """Get full details plus per-date availability and prices for one specific VeryChic offer.

        When to use: after `verychic_list_deals` or `verychic_search_offers` returned an
        offer you want to inspect — pass that offer's `source` and `external_id` here. You
        must obtain those two identifiers from a list/search result first; this tool does
        not search.

        Behaviour: read-only and anonymous; rate-limited to about 1 request per second;
        prices in EUR, text in French. Availability is looked up for roughly the next 5
        months. For tour-operator packages (`source` = 'ORCHESTRA_TO') VeryChic exposes no
        date-availability endpoint: `availabilities` is then empty and
        `availabilities_supported` is false — meaning "not supported", NOT "sold out".

        Returns an object with: `offer` (same fields as a list result, plus `offer_url`),
        `advantages`, `included_added_values`, `non_included_added_values`, `gallery`
        (image URLs), `availabilities` (one entry per check-in date with `date`, `price`,
        `currency`, `nights`, `days`, `departure_city_code`), `availabilities_supported`
        (bool), and `cheapest_price` (lowest available price, or null when none).
        """
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
