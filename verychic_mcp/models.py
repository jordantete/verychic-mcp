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
    opinion_count: int | None = None
    rating_location: float | None = None
    rating_public_area: float | None = None
    rating_room: float | None = None
    rating_service: float | None = None
    rating_food: float | None = None
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
class MonthPrice:
    month: str
    min_price: int
    currency: str
    dates_available: int


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

    @property
    def availabilities_by_month(self) -> list[MonthPrice]:
        """The cheapest check-in date per month, chronologically.

        Lets a caller answer "which month is cheapest" over a wide window without
        carrying every single date: the raw list runs to a few hundred entries.
        """
        grouped: dict[str, list[Availability]] = {}
        for a in self.availabilities:
            # dates are "DD/MM/YYYY"; a priceless or shapeless one says nothing usable
            if a.price is None or a.date.count("/") != 2:
                continue
            grouped.setdefault(a.date.split("/", 1)[1], []).append(a)
        months = []
        for month, items in grouped.items():
            cheapest = min(items, key=lambda a: a.price)
            months.append(MonthPrice(month, cheapest.price, cheapest.currency, len(items)))
        # Sort on (year, month): "MM/YYYY" compared as text puts 01/2027 before 09/2026.
        months.sort(key=lambda m: (m.month[-4:], m.month[:2]))
        return months


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
    opinion_count: int | None
    rating_location: float | None
    rating_public_area: float | None
    rating_room: float | None
    rating_service: float | None
    rating_food: float | None
    distance_km: float | None
    offer_url: str | None


class MonthPriceOut(TypedDict):
    month: str
    min_price: int
    currency: str
    dates_available: int


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
    availabilities_by_month: list[MonthPriceOut]
    availabilities_supported: bool
    cheapest_price: int | None
