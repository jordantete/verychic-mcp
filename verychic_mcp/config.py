"""Configuration constants (routes, parameters, limits)."""
from __future__ import annotations

API_BASE = "https://api.verychic.com/verychic-endpoints/v1"
SEARCH_BASE = "https://search.verychic.com"
SITE_BASE = "https://www.verychic.fr"

CHANNEL = "B2C_HOTEL"
# Channel version captured in Phase 0; auto-discovery refreshes it, this is the safety net.
CHANNEL_VERSION_FALLBACK = "26.06.18.00"

# Common parameters for product calls. memberStatus="PROSPECT" = anonymous visitor
# (valid enum value; "P" is rejected with 422 — confirmed by the network smoke test).
PRODUCT_PARAMS = {
    "branding": "VRC",
    "currency": "EUR",
    "language": "fr",
    "memberStatus": "PROSPECT",
}

RATE_LIMIT_MIN_INTERVAL = 1.0  # minimum seconds between two outgoing requests
HTTP_TIMEOUT = 25              # seconds
IMPERSONATE = "chrome"          # curl_cffi TLS fingerprint
