<div align="center">

<img src="https://raw.githubusercontent.com/jordantete/verychic-mcp/main/assets/logo.png" alt="VeryChic MCP" width="96" height="96" />

# VeryChic MCP

### Search VeryChic hotel deals from any MCP client

Browse current flash-sale offers, filter them by destination or price, and read an
offer's availability and prices by date. Read-only, anonymous, no account needed.

<br>

[![PyPI version](https://img.shields.io/pypi/v/verychic-mcp.svg?style=flat-square)](https://pypi.org/project/verychic-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/actions/workflow/status/jordantete/verychic-mcp/release.yml?style=flat-square&label=release)](https://github.com/jordantete/verychic-mcp/actions/workflows/release.yml)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-7C3AED?style=flat-square)](https://modelcontextprotocol.io)

<br>

[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_server-000000?style=flat-square&logo=cursor&logoColor=white)](https://cursor.com/install-mcp?name=verychic&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJ2ZXJ5Y2hpYy1tY3AiXX0=)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=verychic&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22verychic-mcp%22%5D%7D)

</div>

---

## Quick start

Add the server to your MCP client config. With [`uv`](https://docs.astral.sh/uv/) installed,
there is nothing to clone or install:

```json
{
  "mcpServers": {
    "verychic": {
      "command": "uvx",
      "args": ["verychic-mcp"]
    }
  }
}
```

This runs the server over stdio, which is what Claude Desktop and Claude Code use. You can
also run it directly:

```bash
uvx verychic-mcp          # stdio (default)
uvx verychic-mcp --help   # all options
```

The same `command`/`args` pair works in every stdio client; only the wrapping config differs.
These configs are for **local clients** (stdio). For cloud clients like claude.ai or Cowork,
which connect over HTTPS instead, see [Use from Claude.ai or Cowork](#use-from-claudeai-or-cowork).

<details>
<summary><b>Claude Code</b> (one-liner)</summary>

```bash
claude mcp add verychic -- uvx verychic-mcp
```

</details>

<details>
<summary><b>Cursor</b> — <code>~/.cursor/mcp.json</code></summary>

```json
{
  "mcpServers": {
    "verychic": {
      "command": "uvx",
      "args": ["verychic-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>VS Code</b> — <code>.vscode/mcp.json</code> (note the <code>servers</code> key)</summary>

```json
{
  "servers": {
    "verychic": {
      "command": "uvx",
      "args": ["verychic-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Windsurf</b> — <code>~/.codeium/windsurf/mcp_config.json</code></summary>

```json
{
  "mcpServers": {
    "verychic": {
      "command": "uvx",
      "args": ["verychic-mcp"]
    }
  }
}
```

</details>

---

## Tools

| Tool | What it returns |
| --- | --- |
| `verychic_list_deals` | The current VeryChic offers, with a configurable limit. |
| `verychic_search_offers` | Offers filtered by `destination` (substring match), `country` (exact match), and `max_price`. |
| `verychic_offer_details` | One offer's content (advantages, gallery) plus its availability and prices by date. |

Every call is read-only and anonymous, with a conservative rate limit built into the client.

---

## Examples

Ask your assistant things like:

- "List the current VeryChic deals."
- "Search VeryChic offers in Spain under 600 euros."
- "Get the details and dated prices for the ORCHESTRA hotel offer 44983."
- "Get the details for the ORCHESTRA_TO package offer 301375." Tour-operator packages bundle
  flights with the hotel, so they do not expose day-by-day prices the way a single hotel does.
  The tool still returns the offer content and advantages, and sets
  `availabilities_supported: false` so an empty `availabilities` reads as "not supported for this
  offer type", not "no dates available".

Offers carry a `source` (`ORCHESTRA` for a hotel, `ORCHESTRA_TO` for a package) and an
`external_id`. Both come back from `verychic_list_deals` and `verychic_search_offers`, so the
assistant can pass them to `verychic_offer_details` on its own.

A `verychic_list_deals` result is a list of offer objects (one shown here, trimmed):

```jsonc
{
  "source": "ORCHESTRA",
  "external_id": 36509,
  "name": "Sofitel New York ****",
  "destination": "New York, États-Unis",
  "country": "États-Unis",
  "price": 182,
  "currency": "EUR",
  "discount": 57.0,
  "sales_mode": "FLASH",
  "offer_end_date": "2026-06-24T23:55+0200",
  "image": "https://.../sofitel-new-york.jpg",
  "advantages": ["Petit-déjeuner inclus", "VeryFlexible : réservez en toute sérénité !"],
  "offer_url": "https://www.verychic.fr/p/36509/etats-unis-new-york-hotel-sofitel-new-york"
}
```

`verychic_offer_details` adds `gallery`, `included_added_values`, a `cheapest_price`, and the
day-by-day `availabilities` for a hotel:

```jsonc
{
  "offer": { "source": "ORCHESTRA", "external_id": 44983, "name": "Hotel Kaktus Playa *****", "...": "..." },
  "cheapest_price": 169,
  "availabilities_supported": true,
  "availabilities": [
    { "date": "20/06/2026", "price": 169, "currency": "EUR", "nights": 1, "days": 2 },
    { "date": "21/06/2026", "price": 169, "currency": "EUR", "nights": 1, "days": 2 }
  ]
}
```

---

## Use from Claude.ai or Cowork

Unlike the local clients in [Quick start](#quick-start), cloud clients such as claude.ai and
Cowork only connect to remote MCP servers over HTTPS, not to a local process. To use VeryChic
MCP there, host it yourself in `streamable-http` mode
(`verychic-mcp --transport streamable-http`, behind HTTPS) and add it as a custom connector,
pasting your deployment URL with the `/mcp` path.

A public instance is deployed for convenience at `https://verychic-mcp.fly.dev/mcp`. Add it as
a custom connector in claude.ai/Cowork, or wire it into a local client that speaks remote MCP:

```json
{
  "mcpServers": {
    "verychic": {
      "url": "https://verychic-mcp.fly.dev/mcp"
    }
  }
}
```

It is best-effort and may be paused or rate-limited at any time — for anything beyond a quick
try, run your own instance with the `uvx` command above or host the `streamable-http` mode.

Listing in Anthropic's official connector directory (next to Booking or Tripadvisor) is out of
scope. That directory is reserved for partner integrations that pass a review this kind of tool
would not.

---

## How it works

The VeryChic web app talks to a public JSON API under
`https://api.verychic.com/verychic-endpoints/v1` (plus `search.verychic.com`). This server
replays those same calls with a browser-like TLS fingerprint (`curl_cffi`), parses the
responses into typed objects, and exposes them as MCP tools. Everything works without logging
in. The one volatile request parameter, `channelVersion`, is read from the live site at startup
and falls back to a known value if that read fails.

---

## Development

```bash
git clone https://github.com/jordantete/verychic-mcp.git && cd verychic-mcp
pip install -e ".[dev]"
pytest                  # offline tests, run against recorded fixtures
pytest -m network       # optional smoke test against the live API, low volume
ruff check verychic_mcp tests
```

Releases are tag-driven. Pushing a `vX.Y.Z` tag runs the tests, builds the package, and
publishes it to PyPI through GitHub Actions with [trusted publishing](https://docs.pypi.org/trusted-publishers/),
so no token is stored anywhere.

---

## Disclaimer

> VeryChic MCP is not affiliated with, endorsed by, or connected to VeryChic or VeryChic SAS.
> It is an independent community tool for personal use that reads VeryChic's public web API the
> same way a browser does. You are responsible for complying with VeryChic's terms of sale,
> notably Article 9 on intellectual property and the database producer's *sui generis* right.
> Use it at your own risk, for personal and low-volume browsing only. Do not use it for bulk
> extraction or redistribution of VeryChic's data.

## License

MIT. See [LICENSE](LICENSE).
