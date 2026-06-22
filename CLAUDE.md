# CLAUDE.md — verychic-mcp

**Unofficial, read-only, anonymous** MCP server for VeryChic hotel offers.
3 tools: `verychic_list_deals`, `verychic_search_offers`, `verychic_offer_details`
(details + availability/prices by date). Plain HTTP (curl_cffi), dual transport
(stdio + streamable-http). Not affiliated with VeryChic — see the disclaimer in `README.md`.

## The 4 principles to apply

1. **Think Before Coding** — make assumptions explicit; if several interpretations exist, present them (don't silently pick one); if something simpler exists, say so; if unclear, stop and ask.
2. **Simplicity First** — minimal code that solves the problem; nothing speculative; no abstraction for a single use; if it's 200 lines for 50, rewrite.
3. **Surgical Changes** — touch only what's needed; don't "improve" adjacent code; match the existing style; flag dead code, don't delete it; clean up only the orphans created by your own changes.
4. **Goal-Driven Execution** — turn the task into verifiable criteria ("fix the bug" → "write a test that reproduces it, then make it pass"); short multi-step plan with per-step verification.

## Commands

```bash
pip install -e ".[dev]"               # install (deps: curl_cffi, mcp[cli])
pytest                                # offline tests (fixtures) — excludes @network
pytest -m network                     # real-network smoke test (hits the live API, low volume)
ruff check verychic_mcp tests         # lint
verychic-mcp --help                   # CLI (stdio / streamable-http transports)
verychic-mcp                          # runs in stdio (default)
python -m build                       # builds the wheel (publishing)
```

**Offline** tests: they run against real JSON fixtures in `tests/fixtures/`
(captured in Phase 0), with no network dependency. The `@network` smoke test is opt-in and
excluded from CI by default (`addopts = "-m 'not network'"`).

## Architecture (one responsibility per module, independently testable)

```
config.py      → constants: routes, PRODUCT_PARAMS, rate-limit, channelVersion fallback
errors.py      → VeryChicError + CloudflareBlocked / NotFound / UpstreamError (actionable messages)
http_client.py → VeryChicClient: curl_cffi session (Chrome fingerprint), injectable rate-limit,
                 classify_block() maps HTTP responses to exceptions. get_json / get_text.
discovery.py   → get_channel_version(): reads channelVersion from the live site, hardcoded fallback
models.py      → Offer / Availability / OfferDetails dataclasses (+ offer_url, cheapest_price)
parsers.py     → raw JSON → models (tolerant to missing fields via .get)
api.py         → list_deals / search_offers / offer_details: composes client + routes + parsers
server.py      → FastMCP: registers the 3 tools, resolve_transport(), main()
```

Call flow: `server` (tool) → `api` (route + params) → `http_client.get_json` → `parsers` → model serialized to a dict.

## VeryChic API specifics

- Unified base: `https://api.verychic.com/verychic-endpoints/v1` (+ `search.verychic.com`).
  Everything is **public/anonymous** (200 without login), **no Cloudflare challenge** (confirmed in Phase 0).
- **`memberStatus=PROSPECT`** = anonymous visitor (valid enum value; `P` is rejected with 422).
  Centralized in `config.PRODUCT_PARAMS` — a single place to change.
- Two `source` types in the catalog, routed differently in `offer_details`:
  - `ORCHESTRA` (hotel) → base `/hotel/{source}/{id}.json`; availability via `/product/.../checkin-availabilities.json` (200).
  - `ORCHESTRA_TO` (tour-operator package) → base `/vacation-package/{source}/{id}.json`; `checkin-availabilities` returns **400** → availability is **best-effort** (catch `NotFound`/`UpstreamError` → `[]`, but let `CloudflareBlocked` propagate).
- Offer page on the site: `https://www.verychic.fr/p/{externalId}/{urlName}` (→ `Offer.offer_url`).
- `channelVersion` (a volatile parameter of `preview.json`) is auto-discovered, with a hardcoded fallback in `config.py`.

## Conventions

- **Read-only, anonymous, low volume**: no credentials, no writes/bookings, rate-limit ≥ 1 s between requests (in `http_client`). Defensive posture: no bulk extraction, no Cloudflare bypass.
- **Actionable errors**: always via the exceptions in `errors.py`, never a raw stack trace.
- **TDD + real fixtures**: for any change to parsers/API, add/extend an offline test on a fixture. A behavior change against the live API is validated via the `@network` smoke test.
- **Language**: all code, inline comments, docstrings, and project docs (this file, README, notes) are written in English (OSS codebase). The only exception is the **JSON fixtures**, which keep real (French) API data — don't translate them. Commit messages stay in French.

## Publishing / Release

Public repo: **https://github.com/jordantete/verychic-mcp**.

PyPI publishing is **automated by `.github/workflows/release.yml`** on pushing a
`v*` tag: `test → build → publish-pypi → github-release`. PyPI auth uses
**Trusted Publishing (OIDC)** — **no token stored**. One-time PyPI setup: a *trusted
publisher* (project `verychic-mcp`, owner `jordantete`, repo `verychic-mcp`, workflow
`release.yml`, environment `pypi`).

Publish a version (SemVer):
```bash
git switch main && git pull
pytest && ruff check verychic_mcp tests   # must pass before tagging
# bump "version" in pyproject.toml (X.Y.Z), then:
git add pyproject.toml && git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```
The workflow does the rest (build + PyPI upload + GitHub Release). Once published,
`uvx verychic-mcp` works without cloning. Never commit a PyPI token.

## Status & tracking

MCP **functional and validated against the live API**, public GitHub repo, release CI in place
(on `main`). Published to PyPI (latest `0.1.1`, `uvx verychic-mcp` works) and deployed remotely on
**Fly.io** (`https://verychic-mcp.fly.dev/mcp`; `fly.toml` is gitignored, kept out of the public
repo). Remaining: wire the connector into Cowork (UI step). Tracked improvements and follow-ups:
the `verychic-mcp` Notion project and `docs/superpowers/` (spec, Phase 0 verdict, plans).
