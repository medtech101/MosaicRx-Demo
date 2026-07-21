"""
Week detection: infers which "week" of the course a newly confirmed lecture
belongs to (Monday-Sunday, matching how most med school blocks are
organized) and estimates its content volume (slide/page count, concept
density) so the scheduler can front-load review of brand-new material.
"""
import datetime as dt

from sqlalchemy.orm import Session

from app.models import Week, Document, Concept, ConceptOccurrence


def _week_bounds(day: dt.date) -> tuple[dt.datetime, dt.datetime]:
    start = day - dt.timedelta(days=day.weekday())  # Monday
    end = start + dt.timedelta(days=6)
    return (
        dt.datetime.combine(start, dt.time.min),
        dt.datetime.combine(end, dt.time.max),
    )


def get_or_create_current_week(db: Session, reference_date: dt.date | None = None) -> Week:
    reference_date = reference_date or dt.date.today()
    start, end = _week_bounds(reference_date)

    week = db.query(Week).filter(Week.start_date == start, Week.end_date == end).first()
    if week is None:
        week = Week(label=f"Week of {start.date().isoformat()}", start_date=start, end_date=end)
        db.add(week)
        db.commit()
        db.refresh(week)
    return week


def assign_document_to_current_week(db: Session, document: Document) -> Week:
    week = get_or_create_current_week(db)
    document.week_id = week.id
    db.commit()
    return week


def estimate_document_volume(db: Session, document: Document) -> dict:
    """Slide/page count plus concept density (unique concepts per unit) -
    used by the plan generator to size new-material review blocks."""
    concept_count = (
        db.query(ConceptOccurrence.concept_id)
        .filter(ConceptOccurrence.document_id == document.id)
        .distinct()
        .count()
    )
    unit_count = max(document.unit_count, 1)
    return {
        "unit_count": document.unit_count,
        "concept_count": concept_count,
        "concept_density": round(concept_count / unit_count, 2),
    }


def get_week_topics(db: Session, week_id: int) -> list[dict]:
    """Concepts newly introduced in this week, with their source documents -
    the "current week's topics" the spec asks to infer from the upload batch."""
    rows = (
        db.query(Concept)
        .join(ConceptOccurrence, ConceptOccurrence.concept_id == Concept.id)
        .filter(ConceptOccurrence.week_id == week_id)
        .distinct()
        .all()
    )
    return [{"concept_id": c.id, "name": c.canonical_name} for c in rows]
