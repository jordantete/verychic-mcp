"""Domain models (serializable dataclasses) and their serialized output shapes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict

from .config import SITE_BASE


@dataclass
class Offer:
    source: str
    external_id: int
    name: str
    destination: str | None = None
    country: str | None = None
    price: float | None = None
    currency: str | None = None
    short_desc: str | None = None
    discount: float | None = None
    url_name: str | None = None
    sales_mode: str | None = None
    offer_end_date: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    image: str | None = None
    advantages: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    stars: int | None = None
    price_label: str | None = None
    price_with_flights: float | None = None
    flights_included: bool = False
    rating: float | None = None
    distance_km: float | None = None

    @property
    def offer_url(self) -> str | None:
        if not self.url_name:
            return None
        return f"{SITE_BASE}/p/{self.external_id}/{self.url_name}"


@dataclass
class Availability:
    date: str
    price: int | None
    currency: str
    nights: int | None
    days: int | None
    departure_city_code: str | None = None


@dataclass
class OfferDetails:
    offer: Offer
    advantages: list[str] = field(default_factory=list)
    included_added_values: list[str] = field(default_factory=list)
    non_included_added_values: list[str] = field(default_factory=list)
    gallery: list[str] = field(default_factory=list)
    availabilities: list[Availability] = field(default_factory=list)
    # False for tour-operator packages (ORCHESTRA_TO): the source has no
    # checkin-availabilities endpoint, so an empty `availabilities` means
    # "not supported", not "no dates available".
    availabilities_supported: bool = True

    @property
    def cheapest_price(self) -> int | None:
        prices = [a.price for a in self.availabilities if a.price is not None]
        return min(prices) if prices else None


# Output shapes — the exact dicts the MCP tools return (the dataclasses above
# serialized with their computed `offer_url` / `cheapest_price` included). They
# give the tools a precise outputSchema, which the dataclasses' @property fields
# cannot do on their own (asdict drops properties).


class OfferOut(TypedDict):
    source: str
    external_id: int
    name: str
    destination: str | None
    country: str | None
    price: float | None
    currency: str | None
    short_desc: str | None
    discount: float | None
    url_name: str | None
    sales_mode: str | None
    offer_end_date: str | None
    latitude: float | None
    longitude: float | None
    image: str | None
    advantages: list[str]
    themes: list[str]
    stars: int | None
    price_label: str | None
    price_with_flights: float | None
    flights_included: bool
    rating: float | None
    distance_km: float | None
    offer_url: str | None


class AvailabilityOut(TypedDict):
    date: str
    price: int | None
    currency: str
    nights: int | None
    days: int | None
    departure_city_code: str | None


class OfferDetailsOut(TypedDict):
    offer: OfferOut
    advantages: list[str]
    included_added_values: list[str]
    non_included_added_values: list[str]
    gallery: list[str]
    availabilities: list[AvailabilityOut]
    availabilities_supported: bool
    cheapest_price: int | None
