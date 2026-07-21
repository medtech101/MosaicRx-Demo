from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routers import (
    ingestion, review, settings as settings_router, graph as graph_router,
    resources as resources_router, scheduler as scheduler_router,
)

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


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "notice": "PERSONAL STUDY USE ONLY. No sharing, publishing, or public links exist in this app.",
    }
