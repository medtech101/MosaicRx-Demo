# Personal Study Agent

A strictly single-user, private study companion for medical school lecture
material. Nothing it processes or generates is ever shared publicly,
published, or transmitted to any third party except the configured LLM API
(used for flashcard generation). There is no share, publish, or public-link
functionality anywhere in this app - that's a hard rule enforced in code,
not just documentation.

## Launch it live (one click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/medtech101/MosaicRx-Demo)

This is a real full-stack app (FastAPI + SQLite + Python NLP), so it can't run
on GitHub Pages - Pages only serves static files. The button above deploys the
**whole** app to a free [Render](https://render.com) web service in ~2 minutes
using the blueprint at the repo root (`render.yaml`). When the deploy flow
asks, pick the branch that contains `study-agent/` (or merge it to your
default branch first); every secret it prompts for is optional. You'll get a
live `https://study-agent-*.onrender.com` URL you can open on any tablet or
phone.

Once it's open on a tablet, use your browser's **Add to Home Screen** - the
app is installable, so it launches fullscreen from the home screen like a
native app.

> Free-tier caveats: the instance sleeps after ~15 min idle (first hit after
> that is slow to wake), and free services have no persistent disk, so your
> SQLite data resets on restart. Attach a paid disk mounted at
> `/app/backend/data` for durable storage.

Prefer to run it yourself instead? See **Launching** below - it's one command.

## Use it on a tablet

The UI is a mobile/tablet-first installable web app. However you reach a running
instance - the Render URL above, or `http://<your-computer's-LAN-IP>:8000` from
`./run.sh` on the same Wi-Fi - open it in the tablet's browser and use **Add to
Home Screen** (Safari: Share -> Add to Home Screen; Chrome: menu -> Install /
Add to Home screen). It then launches fullscreen from the home screen with its
own icon, like a native app. Layouts are verified at iPad portrait and
landscape sizes.

## Modules

1. **Ingestion & de-identification** (`backend/app/services/sanitize`) -
   PPTX/PDF/DOCX parsing, blocklist + NER redaction, metadata scrubbing,
   logo/watermark removal, OCR-based image flagging, and a review queue
   before anything is confirmed. Original uploads are deleted the moment
   sanitization is confirmed.
2. **Knowledge graph** (`backend/app/services/graphs`) - biomedical concept
   extraction, a networkx co-occurrence graph, betweenness centrality for
   "bridge concepts," and Louvain clustering. Rendered as a force-directed
   graph in the `/graph` page.
3. **Resource enrichment** (`backend/app/services/resources`) - PubMed
   review articles + NCBI Bookshelf/StatPearls via the free E-utilities API,
   OpenStax/MedlinePlus links, and a link-only commercial-platform mapping
   table (AMBOSS/Boards and Beyond/Bootcamp), with per-resource ratings.
4. **Weekly scheduler** (`backend/app/services/scheduler`) - week detection,
   an SM-2 spaced-repetition model per concept, front-loaded new material,
   exam-date taper mode, and ICS export.
5. **Export center** (`backend/app/services/export`) - sanitized notes
   (MD/PDF), the graph (GraphML/JSON/PNG), bridge/cluster reports, Anki
   flashcards, schedules, and resource ratings - individually or as one ZIP.
   Every artifact is re-scanned against the blocklist immediately before
   download.

## Launching (one command)

The backend serves the built React app itself, so the whole thing runs as a
single server on a single URL - no separate frontend process, nothing to
deploy in two pieces.

```bash
cd study-agent
./run.sh
```

That builds the frontend, installs the backend, best-effort downloads the NLP
models, and starts the server on `http://0.0.0.0:8000`.

- On this machine: open **http://localhost:8000**
- **On your phone** (same Wi-Fi): open **http://<this-machine's-LAN-IP>:8000**
  (e.g. `http://192.168.1.42:8000`). The UI is mobile-first, so this is the
  intended way to use it between classes.

Useful overrides: `PORT=9000 ./run.sh`, `SKIP_BUILD=1 ./run.sh` (reuse an
existing build for fast restarts), `SKIP_MODELS=1 ./run.sh`.

## Launching with Docker

Deploys to any container host (Render, Railway, Fly.io, a VPS, ...):

```bash
cd study-agent
docker build -t study-agent .
docker run -p 8000:8000 \
  -e LLM_API_KEY=sk-... \
  -v "$(pwd)/data:/app/backend/data" \
  study-agent
```

The `-v` mount keeps your SQLite database and sanitized notes on the host so
they survive container restarts. Open `http://localhost:8000`.

## Dev mode (two servers, hot reload)

For working on the frontend with hot-reload, run the two servers separately -
Vite proxies `/api` to the backend:

```bash
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in LLM_API_KEY etc. if you have them
uvicorn app.main:app --reload   # API on :8000

# in another terminal
cd frontend && npm install && npm run dev   # UI on :5173
```

## Secrets

Provide these as environment variables (a `.env` file in `backend/` locally,
`-e` flags or your host's secret manager in Docker). Never commit real keys.

| Secret | Required? | Purpose |
|---|---|---|
| `LLM_API_KEY` | optional | Flashcard generation. Falls back to a template-based generator without it. |
| `NCBI_EMAIL` / `NCBI_API_KEY` | optional | Raises the PubMed/Bookshelf lookup rate limit. Works anonymously without it. |
| `AMBOSS_API_KEY` / `BNB_API_KEY` / `BOOTCAMP_API_KEY` | optional | None of these platforms currently publish a public API - these are stubbed for if/when one exists. Link-only mode works without them. |

## NLP models (automatic, with a fallback)

`run.sh` and the Dockerfile both try to download the spaCy and scispaCy
models automatically, so on a normal internet connection you don't have to do
anything. This app was originally built in a sandbox whose network policy
blocks GitHub-release / HuggingFace / S3 downloads (where those models are
hosted), so it's designed to **run either way**: without the models it falls
back to a coarser regex/heuristic matcher for name detection and concept
extraction, and logs a loud warning saying so. De-identification and concept
extraction are meaningfully better with the real models, but nothing breaks
without them.

To install them by hand into an existing environment:

```bash
python -m spacy download en_core_web_sm
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_md-0.5.4.tar.gz
```

Check `uvicorn`'s startup/request logs to confirm which mode is active.

## Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

32 tests cover the sanitization pipeline (a synthetic lecture fixture with
every kind of leak the pipeline must catch), the co-word graph and bridge-
concept detection (a synthetic three-lecture renal/cardio/pharm corpus),
resource enrichment (PubMed parsing against a mocked transport, since this
build environment can't reach NCBI; link-only commercial mode; rating-based
ranking), the scheduler (week bucketing, SM-2 behavior, taper mode,
completed-block preservation across regeneration), and the export center
(LLM client key-gating and blocklist enforcement, every export format, and
the final blocklist scan refusing a manually-injected leak).
