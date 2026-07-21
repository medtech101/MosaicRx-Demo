import datetime as dt

from ics import Calendar, Event
from sqlalchemy.orm import Session

from app.models import ScheduleBlock

BLOCK_TYPE_LABEL = {"new": "New material", "review": "Spaced review", "taper": "Exam taper review"}


def build_calendar(blocks: list[ScheduleBlock]) -> Calendar:
    cal = Calendar()
    for b in blocks:
        event = Event()
        event.name = f"[{BLOCK_TYPE_LABEL.get(b.block_type, b.block_type)}] {b.label or ''}"
        event.begin = b.day
        event.duration = dt.timedelta(minutes=b.duration_minutes)
        event.description = f"Status: {b.status}" + (
            f" - confidence {b.confidence_rating}/4" if b.confidence_rating else ""
        )
        cal.events.add(event)
    return cal


def export_week_ics(db: Session, week_id: int | None = None) -> str:
    query = db.query(ScheduleBlock)
    if week_id is not None:
        query = query.filter(ScheduleBlock.week_id == week_id)
    blocks = query.all()
    return build_calendar(blocks).serialize()
