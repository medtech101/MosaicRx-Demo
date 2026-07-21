import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Concept, Resource, ResourceRating
from app.services.resources.pubmed import search_pubmed_reviews, search_bookshelf
from app.services.resources.static_links import static_open_resources
from app.services.resources.commercial_links import build_commercial_links, get_templates, set_template

router = APIRouter(prefix="/api/resources", tags=["resources"])

CACHE_TTL = dt.timedelta(days=30)


def _get_concept_or_404(concept_id: int, db: Session) -> Concept:
    concept = db.get(Concept, concept_id)
    if not concept:
        raise HTTPException(404, "Concept not found")
    return concept


def _upsert_resource(db: Session, concept_id: int, source: str, title: str, url: str, summary: str | None) -> Resource:
    row = (
        db.query(Resource)
        .filter(Resource.concept_id == concept_id, Resource.source == source, Resource.url == url)
        .first()
    )
    if row:
        row.title, row.summary, row.fetched_at = title, summary, dt.datetime.utcnow()
    else:
        row = Resource(concept_id=concept_id, source=source, title=title, url=url,
                        summary=summary, fetched_at=dt.datetime.utcnow())
        db.add(row)
        db.flush()
    return row


def _refresh_open_resources(db: Session, concept: Concept) -> None:
    for r in search_pubmed_reviews(concept.canonical_name):
        _upsert_resource(db, concept.id, r.source, r.title, r.url, r.summary)
    for r in search_bookshelf(concept.canonical_name):
        _upsert_resource(db, concept.id, r.source, r.title, r.url, r.summary)
    for r in static_open_resources(concept.canonical_name):
        _upsert_resource(db, concept.id, r["source"], r["title"], r["url"], None)
    db.commit()


def _ensure_commercial_resources(db: Session, concept: Concept) -> list[Resource]:
    links = build_commercial_links(db, concept.canonical_name)
    rows = []
    for link in links:
        rows.append(_upsert_resource(db, concept.id, link["platform"], link["label"], link["url"], None))
    db.commit()
    return rows


def _ensure_resources_populated(db: Session, concept: Concept) -> None:
    cached = db.query(Resource).filter(Resource.concept_id == concept.id).all()
    api_sourced_fetch_times = [r.fetched_at for r in cached if r.source in ("pubmed", "bookshelf")]
    has_open_sources = any(r.source in ("pubmed", "bookshelf", "openstax", "medlineplus") for r in cached)
    is_stale = not api_sourced_fetch_times or min(api_sourced_fetch_times) < dt.datetime.utcnow() - CACHE_TTL

    if not has_open_sources or is_stale:
        _refresh_open_resources(db, concept)
    if not any(r.source in ("amboss", "boards_and_beyond", "bootcamp") for r in cached):
        _ensure_commercial_resources(db, concept)


@router.get("/concepts/{concept_id}")
def get_resources_for_concept(concept_id: int, db: Session = Depends(get_db)):
    concept = _get_concept_or_404(concept_id, db)
    _ensure_resources_populated(db, concept)
    return _serialize_resources(db, concept_id)


@router.post("/concepts/{concept_id}/refresh")
def refresh_resources(concept_id: int, db: Session = Depends(get_db)):
    concept = _get_concept_or_404(concept_id, db)
    _refresh_open_resources(db, concept)
    _ensure_commercial_resources(db, concept)
    return _serialize_resources(db, concept_id)


@router.get("/concepts/{concept_id}/ranked")
def get_ranked_resources(concept_id: int, db: Session = Depends(get_db)):
    """Prioritizes resources the user previously tagged as helpful, then
    unrated resources, then ones tagged not-helpful last."""
    concept = _get_concept_or_404(concept_id, db)
    _ensure_resources_populated(db, concept)
    return _serialize_resources(db, concept_id, ranked=True)


def _serialize_resources(db: Session, concept_id: int, ranked: bool = False) -> dict:
    resources = db.query(Resource).filter(Resource.concept_id == concept_id).all()
    ratings = db.query(ResourceRating).filter(ResourceRating.concept_id == concept_id).all()
    rating_by_resource: dict[int, list[bool]] = {}
    for r in ratings:
        rating_by_resource.setdefault(r.resource_id, []).append(r.helpful)

    def score(res: Resource) -> tuple:
        votes = rating_by_resource.get(res.id, [])
        helpful_count = sum(1 for v in votes if v)
        not_helpful_count = sum(1 for v in votes if not v)
        # higher is better: helpful votes first, then no signal, then explicit not-helpful
        return (-(helpful_count - not_helpful_count), 0 if not votes else 1)

    items = [
        {
            "id": r.id,
            "source": r.source,
            "title": r.title,
            "url": r.url,
            "summary": r.summary,
            "helpful_count": sum(1 for v in rating_by_resource.get(r.id, []) if v),
            "not_helpful_count": sum(1 for v in rating_by_resource.get(r.id, []) if not v),
        }
        for r in resources
    ]
    if ranked:
        items.sort(key=lambda item: score(next(r for r in resources if r.id == item["id"])))

    return {"concept_id": concept_id, "resources": items}


class RatingIn(BaseModel):
    resource_id: int
    concept_id: int
    helpful: bool
    note: str | None = None


@router.post("/ratings")
def rate_resource(payload: RatingIn, db: Session = Depends(get_db)):
    resource = db.get(Resource, payload.resource_id)
    if not resource:
        raise HTTPException(404, "Resource not found")
    rating = ResourceRating(
        resource_id=payload.resource_id, concept_id=payload.concept_id,
        helpful=payload.helpful, note=payload.note,
    )
    db.add(rating)
    db.commit()
    return {"ok": True}


@router.get("/commercial-templates")
def get_commercial_templates(db: Session = Depends(get_db)):
    return get_templates(db)


class TemplateIn(BaseModel):
    url_template: str


@router.put("/commercial-templates/{platform}")
def update_commercial_template(platform: str, payload: TemplateIn, db: Session = Depends(get_db)):
    if "{query}" not in payload.url_template:
        raise HTTPException(400, "Template must contain a {query} placeholder")
    return set_template(db, platform, payload.url_template)
