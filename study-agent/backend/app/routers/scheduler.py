import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Week, ScheduleBlock
from app.services.scheduler.week_detector import get_or_create_current_week, get_week_topics
from app.services.scheduler.plan_generator import generate_schedule
from app.services.scheduler.sm2 import get_or_create_review_state, apply_confidence_rating
from app.services.scheduler.ics_export import export_week_ics, scannable_ics_text
from app.services.sanitize.blocklist import find_blocklist_matches
from .settings import terms_by_category

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


def _serialize_week(week: Week) -> dict:
    return {
        "id": week.id, "label": week.label,
        "start_date": week.start_date.date().isoformat(),
        "end_date": week.end_date.date().isoformat(),
    }


def _serialize_block(b: ScheduleBlock) -> dict:
    return {
        "id": b.id, "week_id": b.week_id, "concept_id": b.concept_id,
        "day": b.day.isoformat(), "duration_minutes": b.duration_minutes,
        "block_type": b.block_type, "status": b.status,
        "confidence_rating": b.confidence_rating, "label": b.label,
    }


@router.get("/weeks")
def list_weeks(db: Session = Depends(get_db)):
    weeks = db.query(Week).order_by(Week.start_date).all()
    return [_serialize_week(w) for w in weeks]


@router.get("/weeks/current")
def current_week(db: Session = Depends(get_db)):
    week = get_or_create_current_week(db)
    return {**_serialize_week(week), "topics": get_week_topics(db, week.id)}


@router.get("/weeks/{week_id}/blocks")
def get_week_blocks(week_id: int, db: Session = Depends(get_db)):
    week = db.get(Week, week_id)
    if not week:
        raise HTTPException(404, "Week not found")
    blocks = db.query(ScheduleBlock).filter(ScheduleBlock.week_id == week_id).order_by(ScheduleBlock.day).all()
    return [_serialize_block(b) for b in blocks]


@router.post("/generate")
def generate(week_id: int | None = None, db: Session = Depends(get_db)):
    week = db.get(Week, week_id) if week_id else get_or_create_current_week(db)
    if not week:
        raise HTTPException(404, "Week not found")
    blocks = generate_schedule(db, week)
    return {"week": _serialize_week(week), "blocks": [_serialize_block(b) for b in blocks]}


class ConfidenceIn(BaseModel):
    rating: int  # 1-4


@router.post("/blocks/{block_id}/confidence")
def submit_confidence(block_id: int, payload: ConfidenceIn, db: Session = Depends(get_db)):
    if payload.rating not in (1, 2, 3, 4):
        raise HTTPException(400, "rating must be 1-4")
    block = db.get(ScheduleBlock, block_id)
    if not block:
        raise HTTPException(404, "Schedule block not found")

    block.status = "completed"
    block.confidence_rating = payload.rating

    if block.concept_id is not None:
        state = get_or_create_review_state(db, block.concept_id)
        apply_confidence_rating(state, payload.rating)

    db.commit()
    return _serialize_block(block)


@router.get("/export.ics", response_class=PlainTextResponse)
def export_ics(week_id: int | None = None, db: Session = Depends(get_db)):
    ics_text = export_week_ics(db, week_id)
    terms = terms_by_category(db)
    matches = find_blocklist_matches(scannable_ics_text(ics_text), terms)
    if matches:
        raise HTTPException(
            422, f"Final blocklist scan found an unresolved term in the calendar: '{matches[0].original}'."
        )
    return ics_text
