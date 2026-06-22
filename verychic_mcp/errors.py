"""Domain exceptions, with actionable default messages."""
from __future__ import annotations


class VeryChicError(Exception):
    """Generic VeryChic-side error."""
    default = "VeryChic error."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default)


class CloudflareBlocked(VeryChicError):
    default = "Blocked by Cloudflare anti-bot protection. Try again later."


class NotFound(VeryChicError):
    default = "VeryChic offer or route not found (it may have expired)."


class UpstreamError(VeryChicError):
    default = "Unexpected response from the VeryChic API (it may have changed)."
