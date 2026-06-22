"""Constantes de configuration (routes, paramètres, limites)."""
from __future__ import annotations

API_BASE = "https://api.verychic.com/verychic-endpoints/v1"
SEARCH_BASE = "https://search.verychic.com"
SITE_BASE = "https://www.verychic.fr"

CHANNEL = "B2C_HOTEL"
# Version de canal capturée en Phase 0 ; l'auto-découverte la rafraîchit, ceci est le filet.
CHANNEL_VERSION_FALLBACK = "26.06.18.00"

# Paramètres communs aux appels produits. memberStatus="PROSPECT" = visiteur anonyme
# (valeur d'enum valide côté API ; "P" est rejeté en 422 — confirmé par le smoke réseau).
PRODUCT_PARAMS = {
    "branding": "VRC",
    "currency": "EUR",
    "language": "fr",
    "memberStatus": "PROSPECT",
}

RATE_LIMIT_MIN_INTERVAL = 1.0  # secondes minimum entre deux requêtes sortantes
HTTP_TIMEOUT = 25              # secondes
IMPERSONATE = "chrome"          # empreinte TLS curl_cffi
