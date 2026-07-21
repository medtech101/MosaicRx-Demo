from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings, BASE_DIR
from app.database import engine, Base
from app.routers import (
    ingestion, review, settings as settings_router, graph as graph_router,
    resources as resources_router, scheduler as scheduler_router, export as export_router,
)

# The production React build, if it exists. When present, this same server
# serves the whole app (UI + API) on one URL/port so it can be launched
# anywhere that runs Python - no separate frontend server needed. In dev you
# instead run `npm run dev` (Vite) which proxies /api here.
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

# import all models so create_all sees the full schema
from app import models  # noqa: F401

app = FastAPI(
    title="Personal Study Agent",
    description=(
        "Strictly single-user, private study companion. Nothing processed or "
        "generated here is ever shared publicly, published, or transmitted to "
        "any third party except the configured LLM API used for summarization "
        "and flashcard generation."
    ),
)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(ingestion.router)
app.include_router(review.router)
app.include_router(settings_router.router)
app.include_router(graph_router.router)
app.include_router(resources_router.router)
app.include_router(scheduler_router.router)
app.include_router(export_router.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "notice": "PERSONAL STUDY USE ONLY. No sharing, publishing, or public links exist in this app.",
    }


# --- serve the built single-page app (only when a production build exists) ---
# Registered LAST so every /api/* route above is matched first.
if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # Never let the catch-all answer for the API namespace - a missing
        # API route should be a real 404, not the HTML shell.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        # Client-side routes (e.g. /graph, /schedule) fall back to index.html
        # so deep links and refreshes work.
        return FileResponse(FRONTEND_DIST / "index.html")

