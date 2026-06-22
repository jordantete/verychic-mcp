"""Transforme le JSON brut VeryChic en modèles de domaine."""
from __future__ import annotations

from .models import Availability, Offer, OfferDetails


def parse_offer(d: dict) -> Offer:
    return Offer(
        source=d.get("source", ""),
        external_id=d.get("externalId"),
        name=d.get("name", ""),
        destination=d.get("destinationName"),
        country=d.get("country"),
        # selon l'endpoint le prix est dans price ou normalizedPrice
        price=d.get("price") if d.get("price") is not None else d.get("normalizedPrice"),
        currency=d.get("currency") or d.get("productCurrency"),
        short_desc=d.get("shortDesc"),
        discount=d.get("discount"),
        url_name=d.get("urlName"),
        sales_mode=d.get("salesMode"),
        offer_end_date=d.get("offerEndDate"),
        latitude=d.get("latitude"),
        longitude=d.get("longitude"),
        image=d.get("image"),
        advantages=list(d.get("advantages") or []),
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


def parse_offer_details(base: dict, preview: dict, avails: list) -> OfferDetails:
    return OfferDetails(
        offer=parse_offer(base),
        advantages=list(preview.get("advantages") or []),
        included_added_values=list(preview.get("includedAddedValues") or []),
        non_included_added_values=list(preview.get("nonIncludedAddedValues") or []),
        gallery=list(preview.get("gallery") or []),
        availabilities=parse_availabilities(avails),
    )
