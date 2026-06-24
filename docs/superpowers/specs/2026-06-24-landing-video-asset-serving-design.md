# Serve the demo video from the app (correct Content-Type)

**Date:** 2026-06-24
**Goal:** Make the demo video on the landing page (`/`) play reliably across
browsers, including Safari/iOS.

## Problem

The landing page `<video>` loads its source from GitHub raw:
`raw.githubusercontent.com/.../assets/connect-claude-desktop.mp4`. GitHub raw
serves `.mp4` with `Content-Type: application/octet-stream` and
`X-Content-Type-Options: nosniff`. With `nosniff`, browsers must not MIME-sniff,
so the resource is not recognized as `video/mp4` — Safari/iOS can refuse to play
it. (The poster, served as `image/png`, is unaffected.)

A secondary, separately-handled fact: the live Fly deployment predates the video
block being added to `landing.py`, so the page is stale and shows no `<video>`
at all. That is fixed by a redeploy (`fly deploy`), which is the operator's
action and out of scope for the code change here.

## Decision

Serve the demo **video and poster** from the Fly app itself, with the correct
`Content-Type`, instead of GitHub raw. The **logo stays on GitHub raw**: it
already serves as `image/png`, and it is also used for `og:image` / favicon,
which require an absolute URL — keeping it avoids needless churn.

## Changes (surgical)

1. **`verychic_mcp/assets.py`** (new, small)
   - `ASSET_MEDIA_TYPES`: whitelist `{filename: media_type}` —
     `connect-claude-desktop.mp4 → video/mp4`,
     `connect-claude-desktop-poster.png → image/png`.
   - `resolve_asset(name) -> Path | None`: returns the file path for a
     whitelisted name if it exists, else `None`. Only whitelisted basenames are
     served, which also forecloses path traversal (`../`, absolute paths).
   - Assets directory resolution: `Path.cwd() / "assets"` (Docker runs the CMD
     from `WORKDIR /app`, where `COPY assets ./assets` lands), with a source-tree
     fallback of `Path(__file__).resolve().parent.parent / "assets"` for running
     from a checkout.

2. **`verychic_mcp/server.py`**
   - New route `@mcp.custom_route("/assets/{name}", methods=["GET"])` returning
     `FileResponse(path, media_type=...)` (Starlette `FileResponse` handles Range
     requests / seeking and `Content-Length` natively) or a 404 `PlainTextResponse`
     when the name is not whitelisted / missing.

3. **`verychic_mcp/landing.py`**
   - `VIDEO_URL = "/assets/connect-claude-desktop.mp4"`
   - `POSTER_URL = "/assets/connect-claude-desktop-poster.png"`
   - Root-relative URLs resolve against the page origin (Fly). `LOGO_URL`
     unchanged.

4. **`Dockerfile`**
   - `COPY assets ./assets` so the files exist in the image at `/app/assets`.

5. **`.dockerignore`**
   - Exclude `assets/connect-claude-desktop.gif` (~4.5 MB, used only by the
     README via GitHub raw) to keep the image lean.

## Tests (offline, TDD — `tests/test_server.py`)

- `GET /assets/connect-claude-desktop.mp4` → 200 and `Content-Type: video/mp4`.
- `GET /assets/connect-claude-desktop-poster.png` → 200 and `image/png`.
- `GET /assets/does-not-exist.mp4` → 404.
- `GET /assets/..%2f..%2fpyproject.toml` (traversal attempt) → 404.
- Landing renders the root-relative `/assets/...` URLs (existing
  `__VIDEO_URL__` / `__POSTER_URL__` token-replacement assertions still pass).

Tests run from the repo root, where `assets/` exists, so `FileResponse` reads the
real files.

## Out of scope

- Moving the logo off GitHub raw (works; `og:image` needs absolute).
- The final `fly deploy` (operator action).

## Post-deploy verification (operator + assistant)

After the operator redeploys, verify against the live landing
(`https://verychic-mcp.fly.dev/`):
- the `<video>` element is present, its source loads (`video/mp4`), and metadata
  decodes (`videoWidth > 0`);
- the page layout stays coherent (full-page screenshot review).

Playwright MCP is not connected in this session; drive the Playwright already
vendored under `demo/node_modules` via a small Node script instead.
