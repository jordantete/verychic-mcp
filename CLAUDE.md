# CLAUDE.md — verychic-mcp

Serveur MCP **non officiel, read-only, anonyme** pour les offres d'hôtels VeryChic.
3 outils : `verychic_list_deals`, `verychic_search_offers`, `verychic_offer_details`
(détail + disponibilité/prix par dates). HTTP pur (curl_cffi), double transport
(stdio + streamable-http). Non affilié à VeryChic — voir le disclaimer du `README.md`.

## Les 4 principes à intégrer

1. **Think Before Coding** — expliciter les hypothèses ; si plusieurs interprétations, les présenter (ne pas trancher en silence) ; si plus simple existe, le dire ; si flou, s'arrêter et demander.
2. **Simplicity First** — code minimal qui résout le problème ; rien de spéculatif ; pas d'abstraction pour usage unique ; si 200 lignes pour 50, réécrire.
3. **Surgical Changes** — ne toucher que le nécessaire ; ne pas « améliorer » le code adjacent ; matcher le style existant ; signaler le dead code, ne pas le supprimer ; nettoyer seulement les orphelins créés par ses propres changements.
4. **Goal-Driven Execution** — transformer la tâche en critères vérifiables (« fix the bug » → « écrire un test qui le reproduit puis le faire passer ») ; plan bref multi-étapes avec vérification par étape.

## Commandes

```bash
pip install -e ".[dev]"               # installer (deps : curl_cffi, mcp[cli])
pytest                                # tests hors-ligne (fixtures) — exclut @network
pytest -m network                     # smoke-test réseau réel (touche l'API live, faible volume)
ruff check verychic_mcp tests         # lint
verychic-mcp --help                   # CLI (transports stdio / streamable-http)
verychic-mcp                          # lance en stdio (défaut)
python -m build                       # construit le wheel (publication)
```

Tests **hors-ligne** : ils tournent sur des fixtures JSON réelles dans `tests/fixtures/`
(capturées en Phase 0), aucune dépendance réseau. Le smoke `@network` est opt-in et
exclu de la CI par défaut (`addopts = "-m 'not network'"`).

## Architecture (une responsabilité par module, testable isolément)

```
config.py      → constantes : routes, PRODUCT_PARAMS, rate-limit, fallback channelVersion
errors.py      → VeryChicError + CloudflareBlocked / NotFound / UpstreamError (messages actionnables)
http_client.py → VeryChicClient : session curl_cffi (empreinte Chrome), rate-limit injectable,
                 classify_block() mappe les réponses HTTP en exceptions. get_json / get_text.
discovery.py   → get_channel_version() : lit channelVersion sur le site live, fallback en dur
models.py      → dataclasses Offer / Availability / OfferDetails (+ offer_url, cheapest_price)
parsers.py     → JSON brut → modèles (tolérant aux champs manquants via .get)
api.py         → list_deals / search_offers / offer_details : compose client + routes + parsers
server.py      → FastMCP : enregistre les 3 outils, resolve_transport(), main()
```

Flux d'un appel : `server` (outil) → `api` (route + params) → `http_client.get_json` → `parsers` → modèle sérialisé en dict.

## Spécificités de l'API VeryChic

- Base unifiée : `https://api.verychic.com/verychic-endpoints/v1` (+ `search.verychic.com`).
  Tout est **public/anonyme** (200 sans login), **pas de challenge Cloudflare** (confirmé en Phase 0).
- **`memberStatus=PROSPECT`** = visiteur anonyme (valeur d'enum valide ; `P` est rejeté en 422).
  Centralisé dans `config.PRODUCT_PARAMS` — un seul endroit à changer.
- Deux types de `source` dans le catalogue, à router différemment dans `offer_details` :
  - `ORCHESTRA` (hôtel) → base `/hotel/{source}/{id}.json` ; dispo via `/product/.../checkin-availabilities.json` (200).
  - `ORCHESTRA_TO` (package tour-op) → base `/vacation-package/{source}/{id}.json` ; `checkin-availabilities` répond **400** → la dispo est **best-effort** (catch `NotFound`/`UpstreamError` → `[]`, mais on laisse remonter `CloudflareBlocked`).
- Page d'offre côté site : `https://www.verychic.fr/p/{externalId}/{urlName}` (→ `Offer.offer_url`).
- `channelVersion` (paramètre volatil de `preview.json`) est auto-découvert, avec fallback en dur dans `config.py`.

## Conventions

- **Read-only, anonyme, faible volume** : aucun credential, aucune écriture/réservation, rate-limit ≥ 1 s entre requêtes (dans `http_client`). Posture défensive : pas d'extraction massive, pas de contournement Cloudflare.
- **Erreurs actionnables** : toujours via les exceptions de `errors.py`, jamais un stacktrace brut.
- **TDD + fixtures réelles** : pour toute évolution des parsers/API, ajouter/étendre un test hors-ligne sur une fixture. Un changement de comportement face à l'API live se valide via le smoke `@network`.
- Messages de commit / docs en français ; README en anglais (convention OSS).

## Publication / Release

Repo public : **https://github.com/jordantete/verychic-mcp**.

La publication PyPI est **automatisée par `.github/workflows/release.yml`** au push d'un
tag `v*` : `test → build → publish-pypi → github-release`. L'auth PyPI se fait par
**Trusted Publishing (OIDC)** — **aucun token stocké**. Setup PyPI une fois : un *trusted
publisher* (projet `verychic-mcp`, owner `jordantete`, repo `verychic-mcp`, workflow
`release.yml`, environnement `pypi`).

Publier une version (SemVer) :
```bash
git switch main && git pull
pytest && ruff check verychic_mcp tests   # doit passer avant de tagger
# bumper "version" dans pyproject.toml (X.Y.Z), puis :
git add pyproject.toml && git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```
Le workflow fait le reste (build + upload PyPI + GitHub Release). Une fois publié,
`uvx verychic-mcp` fonctionne sans cloner. Ne jamais committer de token PyPI.

## État & suivi

MCP **fonctionnel et validé contre l'API live**, repo GitHub public, CI de release en place
(sur `main`). Reste : 1ère publication PyPI (config trusted publisher + tag) et déploiement
remote pour Cowork. Améliorations notées et suivi : projet Notion `verychic-mcp` et
`docs/superpowers/` (spec, verdict Phase 0, plans).
