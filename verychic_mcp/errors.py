"""Exceptions du domaine, avec messages par défaut actionnables."""
from __future__ import annotations


class VeryChicError(Exception):
    """Erreur générique côté VeryChic."""
    default = "Erreur VeryChic."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default)


class CloudflareBlocked(VeryChicError):
    default = "Accès bloqué par la protection anti-bot Cloudflare. Réessaie plus tard."


class NotFound(VeryChicError):
    default = "Offre ou route VeryChic introuvable (elle a peut-être expiré)."


class UpstreamError(VeryChicError):
    default = "Réponse inattendue de l'API VeryChic (elle a peut-être changé)."
