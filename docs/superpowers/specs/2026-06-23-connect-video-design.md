# Demo video — Connect VeryChic MCP to Claude Desktop

**Date:** 2026-06-23
**Goal:** Produce a short, polished demo video showing how to connect the VeryChic
MCP server to **Claude Desktop** and use it. The video must embed both in
`README.md` (GitHub) and in the landing page served at the site root.

## Decisions (locked with the user)

- **Client shown:** Claude Desktop (local, stdio via `uvx verychic-mcp`).
- **Production method:** an **animated recreation** of the Claude Desktop UI
  (HTML/CSS/JS), captured to video via **Playwright's native recorder**. We do
  *not* drive the real app (GUI automation is brittle, model latency is
  nondeterministic). This is a faithful recreation, not a real screen capture —
  acknowledged and accepted.
- **Authentic data:** the demo conversation uses **real VeryChic offers** pulled
  live via the connector (Spain < 600 €), e.g. *Hilton Mallorca Galatzo 5★ — 144 €*,
  *htop Amaika 4★ — 89 €*, *Augusta Club 4★ — 86 €*.
- **Output formats:** one render → **MP4 (H.264, faststart)** for the landing-page
  `<video>` and README `<video>` embed, **plus an optimized GIF** as the
  guaranteed-inline README fallback (GitHub does not reliably play committed MP4
  via `![]()`). A **poster PNG** (first frame) accompanies the MP4.

## Storyboard (~30 s)

1. **Intro (~2 s)** — VeryChic MCP logo + title *"Connect VeryChic to Claude Desktop"*.
2. **Connect (~12 s)** — Settings → Developer → *Edit Config*; the
   `claude_desktop_config.json` fills in (typing animation) with:
   ```json
   { "mcpServers": { "verychic": { "command": "uvx", "args": ["verychic-mcp"] } } }
   ```
   Restart → the three `verychic_*` tools appear in the tools panel.
3. **Live demo (~15 s)** — user asks *"Find VeryChic deals in Spain under €600"*;
   the `verychic_search_offers` tool call animates (running → done); the assistant
   replies with the real offers above (name, stars, price, one advantage).
4. **Outro (~3 s)** — `uvx verychic-mcp` + repo / PyPI links.

## Components (one responsibility each)

```
demo/index.html        → the recreated Claude Desktop UI shell (static markup)
demo/style.css         → faithful Claude Desktop styling (light theme, fonts, layout)
demo/data.js           → the real VeryChic offers + the config snippet (single source of data)
demo/scene.js          → the timeline/animation engine: drives steps, typing, cursor, tool-call states; signals "done"
demo/record.mjs        → Playwright script: open page at fixed viewport, run scene, record video → webm
scripts/encode.sh      → ffmpeg: webm → mp4 (H.264 faststart) + optimized gif + poster png
```

Call flow: `record.mjs` opens `index.html`, waits for `scene.js` to signal
completion, stops the recorder → `webm`; `encode.sh` derives `mp4` / `gif` / `poster`.

## Verification (goal-driven)

- `record.mjs` produces a non-empty `.webm` of expected duration (~30 s).
- `encode.sh` produces a playable `.mp4`, a `.gif` under a sane size budget
  (target ≤ ~8 MB; shorten/loop the highlight if needed), and a `poster.png`.
- Visual check: open the MP4 and confirm the three scenes render, text is legible
  at the chosen resolution, and the real offer data appears correctly.
- README + landing-page embed snippets are provided (not necessarily wired in this
  pass unless approved).

## Out of scope

- Voice-over / audio (silent demo; captions/labels carry the narrative).
- Driving the real Claude Desktop app.
- Publishing the asset to a CDN / GitHub release (we commit files into the repo or
  `assets/`, and provide embed snippets).

## Open choices (sensible defaults taken)

- **Resolution:** 1280×800 (Desktop-like aspect, crisp for README/landing).
- **Theme:** Claude Desktop **light** theme.
- **Asset location:** `assets/` for final `mp4`/`gif`/`poster`; `demo/` for sources.
