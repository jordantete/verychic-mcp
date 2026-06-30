"""Guard against version drift across the project's manifests.

The version lives in several files that must agree: `pyproject.toml` (the source of
truth that gets published to PyPI), `server.json` (top-level and the PyPI package entry,
used by MCP registries like Glama), and the Cursor plugin manifest. Bumping one and
forgetting the others ships an inconsistent release — this test fails the build first.
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def _json_path(rel: str, *keys) -> str:
    obj = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    for k in keys:
        obj = obj[k]
    return obj


def test_version_is_consistent_across_manifests():
    version = _pyproject_version()
    assert _json_path("server.json", "version") == version, "server.json top-level version"
    assert _json_path("server.json", "packages", 0, "version") == version, "server.json package"
    assert _json_path(".cursor-plugin/plugin.json", "version") == version, "cursor plugin"
