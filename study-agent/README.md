# Personal Study Agent

A strictly single-user, private study companion for medical school lecture
material. Nothing it processes or generates is ever shared publicly,
published, or transmitted to any third party except the configured LLM API
(used for flashcard generation). There is no share, publish, or public-link
functionality anywhere in this app - that's a hard rule enforced in code,
not just documentation.

This lives alongside the unrelated MosaicRx investor demo already in this
repo (`../app`, `../index.html`) - the two are independent projects sharing
a repo, not the same product.

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

## Running locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in LLM_API_KEY etc. if you have them
uvicorn app.main:app --reload

# in another terminal
cd frontend
npm install
npm run dev
```

Open the frontend dev server URL (printed by `npm run dev`, default
`http://localhost:5173`).

## Deploying on Replit

Set every secret below under the Secrets tool instead of a `.env` file -
Replit injects them as environment variables automatically:

| Secret | Required? | Purpose |
|---|---|---|
| `LLM_API_KEY` | optional | Flashcard generation. Falls back to a template-based generator without it. |
| `NCBI_EMAIL` / `NCBI_API_KEY` | optional | Raises the PubMed/Bookshelf lookup rate limit. Works anonymously without it. |
| `AMBOSS_API_KEY` / `BNB_API_KEY` / `BOOTCAMP_API_KEY` | optional | None of these platforms currently publish a public API - these are stubbed for if/when one exists. Link-only mode works without them. |

### One-time model download (do this on Replit, not in a restricted sandbox)

This app was built and tested in a sandboxed environment whose network
policy blocks GitHub-release, HuggingFace, and S3 downloads - exactly where
spaCy and scispaCy host their pretrained models. Everything was built
against that constraint with graceful, clearly-logged fallbacks (a coarse
regex/heuristic matcher instead of real NER), so the app **runs** without
the models - but de-identification and concept extraction are meaningfully
better with them. Wherever you actually deploy this (Replit has normal
internet access), run once:

```bash
python -m spacy download en_core_web_sm
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_md-0.5.4.tar.gz
```

Until you do, the app logs a loud warning identifying which fallback is
active - check `uvicorn`'s startup/request logs if you want to confirm
which mode you're running in.

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
