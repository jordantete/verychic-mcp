"""Landing page served at ``/`` (also carries the favicon link).

Pure presentation: a single self-contained HTML document (CDN fonts, inline
CSS/JS, no build step). ``render_landing`` injects the live endpoint URL.
"""
from __future__ import annotations

# Public project links (the logo is already served from the repo, see README header).
LOGO_URL = "https://raw.githubusercontent.com/jordantete/verychic-mcp/main/assets/logo.png"
WEBSITE_URL = "https://github.com/jordantete/verychic-mcp"
PYPI_URL = "https://pypi.org/project/verychic-mcp/"
# Demo video (served from the repo over raw, like the logo above).
VIDEO_URL = "https://raw.githubusercontent.com/jordantete/verychic-mcp/main/assets/connect-claude-desktop.mp4"
POSTER_URL = "https://raw.githubusercontent.com/jordantete/verychic-mcp/main/assets/connect-claude-desktop-poster.png"

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VeryChic MCP: hotel deals for any MCP client</title>
<meta name="description" content="Unofficial, read-only MCP server for VeryChic hotel offers. Search flash-sale deals, filter by destination or price, and read availability and prices by date from any MCP client.">
<meta property="og:title" content="VeryChic MCP">
<meta property="og:description" content="Search VeryChic flash-sale hotel deals from any MCP client.">
<meta property="og:image" content="__LOGO_URL__">
<link rel="icon" type="image/png" href="__LOGO_URL__">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Hanken+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0c0a09; --ink:#f4ece1; --muted:#a99d8d; --faint:#6f6557;
  --gold:#d8b27a; --gold-2:#ecd2a8; --teal:#7fa6a3;
  --line:rgba(216,178,122,.16); --line-2:rgba(216,178,122,.30);
  --panel:rgba(255,255,255,.025); --panel-2:rgba(255,255,255,.045);
  --serif:'Fraunces',Georgia,'Times New Roman',serif;
  --sans:'Hanken Grotesk',system-ui,-apple-system,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,Menlo,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; color:var(--ink); font-family:var(--sans);
  font-size:17px; line-height:1.6; letter-spacing:.005em;
  background:
    radial-gradient(1100px 620px at 12% -8%, rgba(216,178,122,.14), transparent 60%),
    radial-gradient(900px 520px at 102% 2%, rgba(150,104,64,.16), transparent 55%),
    radial-gradient(820px 820px at 50% 128%, rgba(96,128,132,.12), transparent 60%),
    var(--bg);
  background-attachment:fixed;
  -webkit-font-smoothing:antialiased;
  overflow-x:hidden;
}
body::before{ /* grain */
  content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity:.05; mix-blend-mode:overlay;
}
.blob{ position:fixed; z-index:0; width:46vw; height:46vw; border-radius:50%;
  filter:blur(90px); opacity:.5; pointer-events:none;
  background:radial-gradient(circle, rgba(216,178,122,.30), transparent 65%);
  top:-12vw; right:-10vw; animation:drift 26s ease-in-out infinite alternate; }
@keyframes drift{ from{transform:translate(0,0) scale(1)} to{transform:translate(-6vw,6vw) scale(1.12)} }

main{ position:relative; z-index:1; max-width:1000px; margin:0 auto; padding:clamp(2rem,6vw,5rem) clamp(1.25rem,5vw,2.5rem) 4rem; }

/* hero */
.hero{ text-align:center; padding-top:clamp(1rem,5vw,3rem); }
.logo-wrap{ position:relative; width:104px; height:104px; margin:1.6rem auto 1.4rem; }
.logo-wrap img{ width:100%; height:100%; border-radius:24px; display:block;
  border:1px solid var(--line-2);
  box-shadow:0 18px 50px rgba(0,0,0,.55), 0 0 0 6px rgba(216,178,122,.06);
  background:#0a0908; }
.logo-wrap::after{ content:""; position:absolute; inset:-26px; border-radius:50%;
  background:radial-gradient(circle, rgba(216,178,122,.30), transparent 60%);
  filter:blur(18px); z-index:-1; }
h1{ font-family:var(--serif); font-weight:400; font-optical-sizing:auto;
  font-size:clamp(2.9rem,9vw,5.6rem); line-height:1; letter-spacing:-.02em;
  margin:.2rem 0 .1rem; padding:.06em .12em; overflow:visible; }
h1 em{ font-style:italic; font-weight:500; display:inline-block; padding-right:.14em;
  background:linear-gradient(120deg,var(--gold-2),var(--gold)); -webkit-background-clip:text;
  background-clip:text; color:transparent; }
.lede{ max-width:46ch; margin:1.2rem auto 0; color:var(--muted); font-size:1.12rem; }
.tags{ font-family:var(--mono); font-size:.78rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--faint); margin-top:1.1rem; }
.tags b{ color:var(--gold); font-weight:500; }

.endpoint{ margin:2.2rem auto 0; max-width:560px; text-align:left; }
.endpoint .label{ font-family:var(--mono); font-size:.68rem; letter-spacing:.24em;
  text-transform:uppercase; color:var(--faint); display:block; margin:0 0 .5rem .2rem; }
.endpoint-row{ display:flex; align-items:center; gap:.6rem; background:var(--panel);
  border:1px solid var(--line); border-radius:14px; padding:.7rem .7rem .7rem 1rem; }
.endpoint-row code{ font-family:var(--mono); font-size:.98rem; color:var(--gold-2);
  flex:1; overflow-x:auto; white-space:nowrap; }
.copy{ font-family:var(--mono); font-size:.72rem; letter-spacing:.08em; cursor:pointer;
  color:var(--ink); background:var(--panel-2); border:1px solid var(--line);
  border-radius:9px; padding:.45rem .7rem; transition:.18s; white-space:nowrap; }
.copy:hover{ border-color:var(--line-2); color:var(--gold-2); transform:translateY(-1px); }
.copy.ok{ color:#0c0a09; background:var(--gold); border-color:var(--gold); }

.cta{ display:flex; gap:.8rem; justify-content:center; margin-top:1.8rem; flex-wrap:wrap; }
.btn{ font-family:var(--mono); font-size:.82rem; letter-spacing:.06em; text-decoration:none;
  color:var(--ink); border:1px solid var(--line-2); border-radius:11px; padding:.7rem 1.2rem;
  transition:.2s; }
.btn:hover{ transform:translateY(-2px); border-color:var(--gold); color:var(--gold-2);
  box-shadow:0 10px 30px rgba(216,178,122,.12); }
.btn.primary{ background:linear-gradient(120deg,var(--gold-2),var(--gold)); color:#0c0a09;
  border-color:transparent; font-weight:500; }
.btn.primary:hover{ color:#0c0a09; box-shadow:0 12px 34px rgba(216,178,122,.30); }

/* demo video */
.demo{ max-width:880px; margin:2.4rem auto 0; border:1px solid var(--line-2); border-radius:18px;
  overflow:hidden; background:#0a0908; box-shadow:0 26px 80px rgba(0,0,0,.55); }
.demo video{ display:block; width:100%; height:auto; }

/* sections */
section{ margin-top:clamp(4rem,9vw,6.5rem); }
.eyebrow{ font-family:var(--mono); font-size:.7rem; letter-spacing:.26em; text-transform:uppercase;
  color:var(--gold); text-align:center; }
h2{ font-family:var(--serif); font-weight:400; font-size:clamp(1.8rem,4.5vw,2.7rem);
  letter-spacing:-.01em; text-align:center; margin:.5rem 0 0; }
.sub{ text-align:center; color:var(--muted); margin:.7rem auto 0; max-width:42ch; }

.grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:2.5rem; }
.card{ position:relative; background:var(--panel); border:1px solid var(--line);
  border-radius:18px; padding:1.6rem 1.4rem 1.5rem; overflow:hidden; transition:.25s; }
.card::before{ content:""; position:absolute; inset:0; opacity:0; transition:.25s;
  background:radial-gradient(420px 200px at 50% -30%, rgba(216,178,122,.16), transparent 70%); }
.card:hover{ transform:translateY(-5px); border-color:var(--line-2); }
.card:hover::before{ opacity:1; }
.card .n{ font-family:var(--serif); font-style:italic; font-size:1.2rem; color:var(--faint); }
.card h3{ font-family:var(--mono); font-size:.96rem; font-weight:500; color:var(--gold-2);
  margin:.7rem 0 .5rem; position:relative; }
.card p{ font-size:.95rem; color:var(--muted); margin:0; position:relative; }

.cols{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:2.5rem; }
.code{ background:var(--panel); border:1px solid var(--line); border-radius:16px; overflow:hidden; }
.code-head{ display:flex; align-items:center; justify-content:space-between;
  padding:.7rem 1rem; border-bottom:1px solid var(--line); }
.code-head span{ font-family:var(--mono); font-size:.72rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--faint); }
.code pre{ margin:0; padding:1.1rem 1.2rem; overflow-x:auto; }
.code code{ font-family:var(--mono); font-size:.86rem; line-height:1.65; color:var(--ink);
  white-space:pre; }
.code .hint{ font-size:.84rem; color:var(--faint); padding:0 1.2rem 1.1rem; margin:.2rem 0 0; }

footer{ margin-top:clamp(4rem,9vw,6rem); padding-top:2rem; border-top:1px solid var(--line);
  text-align:center; color:var(--faint); font-size:.88rem; }
footer a{ color:var(--muted); text-decoration:none; border-bottom:1px solid var(--line); }
footer a:hover{ color:var(--gold-2); border-color:var(--line-2); }
.disclaimer{ font-family:var(--mono); font-size:.72rem; letter-spacing:.08em; margin-bottom:.6rem; }

/* motion */
.reveal{ opacity:0; transform:translateY(18px); animation:rise .9s cubic-bezier(.2,.7,.2,1) forwards; }
@keyframes rise{ to{ opacity:1; transform:none; } }
@media (prefers-reduced-motion:reduce){ .reveal{animation:none;opacity:1;transform:none} .blob{animation:none} }

@media (max-width:760px){
  .grid,.cols{ grid-template-columns:1fr; }
}
</style>
</head>
<body>
<div class="blob"></div>
<main>
  <header class="hero">
    <div class="logo-wrap reveal" style="animation-delay:.08s"><img src="__LOGO_URL__" alt="VeryChic MCP logo"></div>
    <h1 class="reveal" style="animation-delay:.14s">VeryChic <em>MCP</em></h1>
    <p class="lede reveal" style="animation-delay:.2s">Search VeryChic flash-sale hotel deals, filter them by destination or price, and read availability and prices by date, straight from any MCP client.</p>
    <p class="tags reveal" style="animation-delay:.26s"><b>Unofficial</b> · <b>Read-only</b> · <b>Anonymous</b></p>
    <div class="endpoint reveal" style="animation-delay:.32s">
      <span class="label">Remote endpoint (HTTPS)</span>
      <div class="endpoint-row">
        <code id="endpoint">__ENDPOINT__</code>
        <button class="copy" data-target="endpoint">Copy</button>
      </div>
    </div>
    <div class="cta reveal" style="animation-delay:.38s">
      <a class="btn primary" href="__WEBSITE_URL__">GitHub ↗</a>
      <a class="btn" href="__PYPI_URL__">PyPI ↗</a>
    </div>
  </header>

  <section>
    <p class="eyebrow reveal">See it in action</p>
    <h2 class="reveal">From config to deals in 30 seconds</h2>
    <p class="sub reveal">Add the server in Claude Desktop, then ask for hotel deals in plain language.</p>
    <div class="demo reveal" style="animation-delay:.06s">
      <video src="__VIDEO_URL__" poster="__POSTER_URL__" controls muted loop playsinline preload="metadata"></video>
    </div>
  </section>

  <section>
    <p class="eyebrow reveal">What it does</p>
    <h2 class="reveal">Three tools, zero account</h2>
    <p class="sub reveal">Every call is read-only and anonymous, with a conservative rate limit built in.</p>
    <div class="grid">
      <div class="card reveal" style="animation-delay:.05s">
        <div class="n">01</div>
        <h3>verychic_list_deals</h3>
        <p>Browse the current VeryChic flash-sale offers, with a configurable limit.</p>
      </div>
      <div class="card reveal" style="animation-delay:.12s">
        <div class="n">02</div>
        <h3>verychic_search_offers</h3>
        <p>Filter offers by destination, country, and maximum price.</p>
      </div>
      <div class="card reveal" style="animation-delay:.19s">
        <div class="n">03</div>
        <h3>verychic_offer_details</h3>
        <p>Full content, gallery, and day-by-day availability and prices for one offer.</p>
      </div>
    </div>
  </section>

  <section>
    <p class="eyebrow reveal">Setup</p>
    <h2 class="reveal">Connect in seconds</h2>
    <div class="cols">
      <div class="code reveal" style="animation-delay:.05s">
        <div class="code-head"><span>Local · stdio</span><button class="copy">Copy</button></div>
        <pre><code>{
  "mcpServers": {
    "verychic": {
      "command": "uvx",
      "args": ["verychic-mcp"]
    }
  }
}</code></pre>
        <p class="hint">Claude Desktop, Claude Code, Cursor, Windsurf…</p>
      </div>
      <div class="code reveal" style="animation-delay:.12s">
        <div class="code-head"><span>Remote · HTTPS</span><button class="copy">Copy</button></div>
        <pre><code>{
  "mcpServers": {
    "verychic": {
      "url": "__ENDPOINT__"
    }
  }
}</code></pre>
        <p class="hint">claude.ai, Cowork, or any remote-MCP client.</p>
      </div>
    </div>
  </section>

  <footer>
    <p class="disclaimer">Not affiliated with VeryChic · MIT licensed</p>
    <p><a href="__WEBSITE_URL__">GitHub</a> &nbsp;·&nbsp; <a href="__PYPI_URL__">PyPI</a> &nbsp;·&nbsp; <a href="https://modelcontextprotocol.io">Model Context Protocol</a></p>
  </footer>
</main>
<script>
(function(){
  function flash(btn,text){ navigator.clipboard.writeText(text).then(function(){
    var o=btn.textContent; btn.textContent='Copied'; btn.classList.add('ok');
    setTimeout(function(){ btn.textContent=o; btn.classList.remove('ok'); },1400);
  }); }
  document.querySelectorAll('.copy').forEach(function(btn){
    btn.addEventListener('click',function(){
      var box=btn.closest('.code');
      var code = box ? box.querySelector('code') : document.getElementById(btn.dataset.target);
      if(code){ flash(btn, code.innerText.trim()); }
    });
  });
})();
</script>
</body>
</html>"""


def render_landing(endpoint: str) -> str:
    """Return the landing page HTML with the live MCP endpoint URL injected."""
    return (_PAGE
            .replace("__LOGO_URL__", LOGO_URL)
            .replace("__WEBSITE_URL__", WEBSITE_URL)
            .replace("__PYPI_URL__", PYPI_URL)
            .replace("__VIDEO_URL__", VIDEO_URL)
            .replace("__POSTER_URL__", POSTER_URL)
            .replace("__ENDPOINT__", endpoint))
