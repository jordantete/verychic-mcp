"""Serveur MCP (FastMCP) exposant 3 outils VeryChic, en double transport."""
from __future__ import annotations

import argparse
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from . import api
from .discovery import get_channel_version
from .http_client import VeryChicClient


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
    mcp = FastMCP("verychic")

    @mcp.tool()
    def verychic_list_deals(limit: int = 20) -> list[dict]:
        """Liste les offres VeryChic du moment (par défaut 20)."""
        return [_offer_dict(o) for o in api.list_deals(client, limit=limit)]

    @mcp.tool()
    def verychic_search_offers(destination: str | None = None, country: str | None = None,
                               max_price: float | None = None, limit: int = 20) -> list[dict]:
        """Recherche/filtre les offres par destination (sous-chaîne), pays et/ou prix max."""
        offers = api.search_offers(client, destination=destination, country=country,
                                   max_price=max_price, limit=limit)
        return [_offer_dict(o) for o in offers]

    @mcp.tool()
    def verychic_offer_details(source: str, external_id: int) -> dict:
        """Détail d'une offre (avantages, galerie) + disponibilités/prix par dates."""
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
