"""Auto-découverte de paramètres volatils (channelVersion) avec fallback en dur."""
from __future__ import annotations

import re

from .config import CHANNEL_VERSION_FALLBACK, SITE_BASE

_VERSION_RE = re.compile(r"channelVersion[\"']?\s*[:=]\s*[\"'](\d\d\.\d\d\.\d\d\.\d\d)")


def extract_channel_version(html: str) -> str | None:
    m = _VERSION_RE.search(html or "")
    return m.group(1) if m else None


def get_channel_version(client, *, fallback: str = CHANNEL_VERSION_FALLBACK) -> str:
    """Best-effort : lit channelVersion depuis la home live ; sinon retourne le fallback."""
    try:
        html = client.get_text(SITE_BASE + "/")
    except Exception:
        return fallback
    return extract_channel_version(html) or fallback
