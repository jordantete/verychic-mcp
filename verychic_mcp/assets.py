"""Static assets served by the app over HTTP (demo video + its poster).

These are served from the app — not GitHub raw — so they carry the correct
``Content-Type``. GitHub raw serves ``.mp4`` as ``application/octet-stream`` with
``nosniff``, which Safari/iOS can refuse to play. Only the whitelisted basenames
below are served, which also forecloses path traversal.
"""
from __future__ import annotations

from pathlib import Path

# Whitelist: basename -> Content-Type. The logo stays on GitHub raw (it already
# serves as image/png and is reused for og:image / favicon, which need an
# absolute URL).
ASSET_MEDIA_TYPES = {
    "connect-claude-desktop.mp4": "video/mp4",
    "connect-claude-desktop-poster.png": "image/png",
}


def _assets_dir() -> Path:
    # Docker runs the CMD from WORKDIR /app, where `COPY assets ./assets` lands.
    cwd_assets = Path.cwd() / "assets"
    if cwd_assets.is_dir():
        return cwd_assets
    # Fallback for running from a source checkout (repo_root/verychic_mcp/..).
    return Path(__file__).resolve().parent.parent / "assets"


def resolve_asset(name: str) -> Path | None:
    """Path for a whitelisted asset if it exists on disk, else ``None``."""
    if name not in ASSET_MEDIA_TYPES:
        return None
    path = _assets_dir() / name
    return path if path.is_file() else None
