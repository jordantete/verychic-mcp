"""API layer: composes the HTTP client, routes, and parsers."""
from __future__ import annotations

from datetime import date

from .config import API_BASE, CHANNEL, PRODUCT_PARAMS
from .errors import NotFound, UpstreamError, VeryChicError
from .geo import haversine_km
from .models import Offer, OfferDetails
from .parsers import parse_offer_details, parse_offers


def _fetch_all_offers(client) -> list[Offer]:
    params = {**PRODUCT_PARAMS, "detailed": "false", "page": 0, "size": 2000, "opinionCount": 0}
    payload = client.get_json(f"{API_BASE}/products.json", params)
    return parse_offers(payload)


# sort_by -> (Offer attribute, descending?). discount/rating/stars: best first.
_SORT_SPEC = {
    "discount": ("discount", True),
    "price": ("price", False),
    "rating": ("rating", True),
    "stars": ("stars", True),
    "distance": ("distance_km", False),
}


def _sort_offers(offers: list[Offer], sort_by: str | None) -> list[Offer]:
    spec = _SORT_SPEC.get(sort_by) if sort_by else None
    if spec is None:
        return offers  # default: catalogue order
    attr, descending = spec

    def key(o: Offer):
        v = getattr(o, attr)
        if v is None:
            return (1, 0.0)  # missing values always sort last
        return (0, -v if descending else v)

    return sorted(offers, key=key)


def list_deals(client, *, limit: int = 20) -> list[Offer]:
    # [DEPRECATED] Thin alias: search with no filter/sort == catalogue order.
    return search_offers(client, limit=limit)


def search_offers(client, *, destination: str | None = None, country: str | None = None,
                  max_price: float | None = None, min_discount: float | None = None,
                  min_stars: int | None = None, flights_included: bool | None = None,
                  theme: str | None = None,
                  near_lat: float | None = None, near_lng: float | None = None,
                  radius_km: float | None = None, sort_by: str | None = None,
                  limit: int = 20) -> list[Offer]:
    # Validate geo params before any network call (actionable, no raw stack trace).
    if (near_lat is None) != (near_lng is None):
        raise VeryChicError(
            "Geo search requires both near_lat and near_lng (provide them together)."
        )
    has_center = near_lat is not None and near_lng is not None
    if not has_center and (radius_km is not None or sort_by == "distance"):
        raise VeryChicError("radius_km and sort_by='distance' require near_lat and near_lng.")

    offers = _fetch_all_offers(client)
    if has_center:
        for o in offers:
            if o.latitude is not None and o.longitude is not None:
                o.distance_km = haversine_km(near_lat, near_lng, o.latitude, o.longitude)
    if destination:
        d = destination.casefold()
        offers = [o for o in offers
                  if d in (o.destination or "").casefold() or d in (o.name or "").casefold()]
    if country:
        c = country.casefold()
        offers = [o for o in offers if (o.country or "").casefold() == c]
    if max_price is not None:
        offers = [o for o in offers if o.price is not None and o.price <= max_price]
    if min_discount is not None:
        offers = [o for o in offers if o.discount is not None and o.discount >= min_discount]
    if min_stars is not None:
        offers = [o for o in offers if o.stars is not None and o.stars >= min_stars]
    if flights_included is not None:
        offers = [o for o in offers if o.flights_included == flights_included]
    if theme:
        offers = [o for o in offers if theme in o.themes]
    if radius_km is not None:
        offers = [o for o in offers if o.distance_km is not None and o.distance_km <= radius_km]
    offers = _sort_offers(offers, sort_by)
    return offers[:limit]


def default_months(n: int = 5, today: date | None = None) -> list[str]:
    today = today or date.today()
    out: list[str] = []
    y, m = today.year, today.month
    for _ in range(n):
        out.append(f"{m:02d}/{y}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def offer_details(client, source: str, external_id: int, *, channel_version: str,
                  months: list[str] | None = None) -> OfferDetails:
    months = months or default_months()
    # Tour-operator packages (ORCHESTRA_TO) are exposed under /vacation-package/
    # and have no checkin-availabilities endpoint (date availability unsupported).
    is_package = source == "ORCHESTRA_TO"
    base_kind = "vacation-package" if is_package else "hotel"
    base = client.get_json(
        f"{API_BASE}/{base_kind}/{source}/{external_id}.json",
        {**PRODUCT_PARAMS, "channel": CHANNEL, "opinionCount": 20},
    )
    preview = client.get_json(
        f"{API_BASE}/product/{source}/{external_id}/fr/preview.json",
        {"opinionCount": 20, "channel": CHANNEL, "channelVersion": channel_version},
    )
    try:
        avails = client.get_json(
            f"{API_BASE}/product/{source}/{external_id}/checkin-availabilities.json",
            {"monthYear": ",".join(months), "channel": CHANNEL},
        )
    except (NotFound, UpstreamError):
        # Packages don't expose date availability (404/400); we do NOT swallow
        # a possible Cloudflare block, which must propagate.
        avails = []
    return parse_offer_details(base, preview, avails, availabilities_supported=not is_package)
