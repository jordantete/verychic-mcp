"""Transforms raw VeryChic JSON into domain models."""
from __future__ import annotations

import re

from .models import Availability, Offer, OfferDetails
from .themes import decode_themes

# Stars appear as a run of asterisks in the name ("Sofitel New York ****"),
# or as "<n>-etoiles" inside the urlName slug. Tolerant: returns None if neither.
_NAME_STARS_RE = re.compile(r"\*{1,5}")
_URL_STARS_RE = re.compile(r"(\d)\s*-?\s*etoiles?")

# transportation values other than "NONE" mean a flight is part of the offer.
_NO_FLIGHT = {"", "NONE", None}


def parse_stars(name: str | None, url_name: str | None) -> int | None:
    if name:
        m = _NAME_STARS_RE.search(name)
        if m:
            return len(m.group(0))
    if url_name:
        m = _URL_STARS_RE.search(url_name)
        if m:
            return int(m.group(1))
    return None


def parse_price_label(d: dict) -> str | None:
    parts = [p for p in (d.get("pricePreLabel"), d.get("pricePostLabel")) if p]
    return " ".join(parts) if parts else None


def parse_flights_included(d: dict) -> bool:
    return d.get("transportation") not in _NO_FLIGHT


def plausible_price(*values: float | None) -> float | None:
    # The live catalogue sometimes returns corrupt non-positive prices (e.g. -50).
    # Pick the first strictly-positive candidate; otherwise the price is unknown.
    for v in values:
        if v is not None and v > 0:
            return v
    return None


def plausible_discount(v: float | None) -> float | None:
    # Discounts outside 0-100% are corrupt (e.g. 263%); treat them as unknown so
    # they are excluded by min_discount and sink to the bottom of sort_by=discount,
    # instead of surfacing as a fake "best deal".
    return v if v is not None and 0 <= v <= 100 else None


def parse_offer(d: dict) -> Offer:
    return Offer(
        source=d.get("source", ""),
        external_id=d.get("externalId"),
        name=d.get("name", ""),
        destination=d.get("destinationName"),
        country=d.get("country"),
        # depending on the endpoint, the price is in price or normalizedPrice;
        # guard against corrupt non-positive values (prefer the first plausible one).
        price=plausible_price(d.get("price"), d.get("normalizedPrice")),
        currency=d.get("currency") or d.get("productCurrency"),
        short_desc=d.get("shortDesc"),
        discount=plausible_discount(d.get("discount")),
        url_name=d.get("urlName"),
        sales_mode=d.get("salesMode"),
        offer_end_date=d.get("offerEndDate"),
        latitude=d.get("latitude"),
        longitude=d.get("longitude"),
        image=d.get("image"),
        advantages=list(d.get("advantages") or []),
        themes=decode_themes(d.get("thematics")),
        stars=parse_stars(d.get("name"), d.get("urlName")),
        price_label=parse_price_label(d),
        # priceWithFlights is 0 (or absent) when there is no flight price; treat as None.
        price_with_flights=d.get("priceWithFlights") or None,
        flights_included=parse_flights_included(d),
        rating=(d.get("opinions") or {}).get("generalGrade"),
    )


def parse_offers(payload: dict) -> list[Offer]:
    return [parse_offer(item) for item in payload.get("content", [])]


def parse_availabilities(items: list) -> list[Availability]:
    out: list[Availability] = []
    for it in items or []:
        out.append(Availability(
            date=it.get("date", ""),
            price=it.get("price"),
            currency=it.get("currency", ""),
            nights=it.get("nights"),
            days=it.get("days"),
            departure_city_code=it.get("departureCityCode"),
        ))
    return out


def parse_offer_details(base: dict, preview: dict, avails: list,
                        availabilities_supported: bool = True) -> OfferDetails:
    return OfferDetails(
        offer=parse_offer(base),
        advantages=list(preview.get("advantages") or []),
        included_added_values=list(preview.get("includedAddedValues") or []),
        non_included_added_values=list(preview.get("nonIncludedAddedValues") or []),
        gallery=list(preview.get("gallery") or []),
        availabilities=parse_availabilities(avails),
        availabilities_supported=availabilities_supported,
    )
