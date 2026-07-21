import csv
import io

from sqlalchemy.orm import Session

from app.models import ScheduleBlock, Week, Resource, ResourceRating, Concept


def schedule_to_csv(db: Session) -> str:
    """Current + historical weekly schedules - every ScheduleBlock ever
    generated, so past weeks stay auditable alongside the current plan."""
    weeks = {w.id: w for w in db.query(Week).all()}
    blocks = db.query(ScheduleBlock).order_by(ScheduleBlock.day).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["week", "day", "block_type", "label", "duration_minutes", "status", "confidence_rating"])
    for b in blocks:
        week = weeks.get(b.week_id)
        writer.writerow([
            week.label if week else b.week_id, b.day.isoformat(), b.block_type,
            b.label or "", b.duration_minutes, b.status, b.confidence_rating or "",
        ])
    return buf.getvalue()


def resource_ratings_to_csv(db: Session) -> str:
    concepts = {c.id: c.canonical_name for c in db.query(Concept).all()}
    resources = db.query(Resource).all()
    ratings = db.query(ResourceRating).all()
    ratings_by_resource: dict[int, list[bool]] = {}
    for r in ratings:
        ratings_by_resource.setdefault(r.resource_id, []).append(r.helpful)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["concept", "source", "title", "url", "helpful_count", "not_helpful_count"])
    for res in resources:
        votes = ratings_by_resource.get(res.id, [])
        writer.writerow([
            concepts.get(res.concept_id, res.concept_id), res.source, res.title, res.url,
            sum(1 for v in votes if v), sum(1 for v in votes if not v),
        ])
    return buf.getvalue()
