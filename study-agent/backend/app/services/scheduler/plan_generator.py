"""
Generates the weekly study plan: front-loads first-pass review of brand-new
material onto the earliest remaining days, interleaves spaced-repetition
review of prior weeks' concepts (per their SM-2 due dates) across the whole
week, and shifts into taper-and-consolidate mode as an exam date approaches.
Regeneration only ever replaces "planned" blocks - anything already marked
"completed" survives, so reactive rescheduling never discards finished work.
"""
import datetime as dt

from sqlalchemy.orm import Session

from app.models import Week, Concept, ConceptReviewState, ScheduleBlock, AppSettingKV
from .week_detector import get_week_topics

DEFAULT_WEEKLY_HOURS = 10
TAPER_WINDOW_DAYS = 14
STUDY_HOUR_OF_DAY = 19  # default evening study slot


def _get_setting(db: Session, key: str, default=None):
    row = db.get(AppSettingKV, key)
    return row.value if row is not None and row.value is not None else default


def _remaining_days(week: Week) -> list[dt.date]:
    today = dt.date.today()
    all_days = [(week.start_date.date() + dt.timedelta(days=i)) for i in range(7)]
    remaining = [d for d in all_days if d >= today]
    return remaining or all_days[-1:]


def _day_datetime(day: dt.date) -> dt.datetime:
    return dt.datetime(day.year, day.month, day.day, STUDY_HOUR_OF_DAY, 0)


def _duration_for_confidence(last_confidence: int | None) -> int:
    if last_confidence in (1, 2):
        return 40
    if last_confidence == 4:
        return 15
    return 25


def generate_schedule(db: Session, week: Week) -> list[ScheduleBlock]:
    weekly_hours = _get_setting(db, "weekly_hours", DEFAULT_WEEKLY_HOURS)
    budget_minutes = int(weekly_hours) * 60

    exam_date_str = _get_setting(db, "exam_date")
    taper_mode = False
    if exam_date_str:
        try:
            exam_date = dt.date.fromisoformat(exam_date_str)
            days_to_exam = (exam_date - dt.date.today()).days
            taper_mode = 0 <= days_to_exam <= TAPER_WINDOW_DAYS
        except ValueError:
            pass

    # Anything already studied this generation should never be wiped.
    db.query(ScheduleBlock).filter(
        ScheduleBlock.week_id == week.id, ScheduleBlock.status == "planned"
    ).delete()

    remaining_days = _remaining_days(week)
    new_topics = get_week_topics(db, week.id)
    new_concept_ids = {t["concept_id"] for t in new_topics}

    due_states = (
        db.query(ConceptReviewState)
        .filter(ConceptReviewState.due_date <= week.end_date, ~ConceptReviewState.concept_id.in_(new_concept_ids or [0]))
        .order_by(ConceptReviewState.due_date)
        .all()
    )

    concepts_by_id = {c.id: c for c in db.query(Concept).all()}
    blocks: list[ScheduleBlock] = []

    if taper_mode:
        # Consolidate: review everything with a review state, weakest first,
        # de-prioritize deep dives into material that's still brand new.
        all_states = db.query(ConceptReviewState).order_by(ConceptReviewState.ease_factor).all()
        used_minutes = 0
        for i, state in enumerate(all_states):
            duration = _duration_for_confidence(state.last_confidence)
            if used_minutes + duration > budget_minutes:
                break
            day = remaining_days[i % len(remaining_days)]
            concept = concepts_by_id.get(state.concept_id)
            blocks.append(ScheduleBlock(
                week_id=week.id, concept_id=state.concept_id, day=_day_datetime(day),
                duration_minutes=duration, block_type="taper", status="planned",
                label=f"Taper review: {concept.canonical_name if concept else state.concept_id}",
            ))
            used_minutes += duration

        # A couple of light new-material passes so nothing is totally ignored.
        for i, topic in enumerate(new_topics[:3]):
            duration = 15
            if used_minutes + duration > budget_minutes:
                break
            day = remaining_days[i % len(remaining_days)]
            blocks.append(ScheduleBlock(
                week_id=week.id, concept_id=topic["concept_id"], day=_day_datetime(day),
                duration_minutes=duration, block_type="taper", status="planned",
                label=f"Quick pass: {topic['name']}",
            ))
            used_minutes += duration
    else:
        used_minutes = 0
        front_load_days = remaining_days[:2] if len(remaining_days) >= 2 else remaining_days
        for i, topic in enumerate(new_topics):
            duration = 30
            if used_minutes + duration > budget_minutes:
                break
            day = front_load_days[i % len(front_load_days)]
            blocks.append(ScheduleBlock(
                week_id=week.id, concept_id=topic["concept_id"], day=_day_datetime(day),
                duration_minutes=duration, block_type="new", status="planned",
                label=f"First pass: {topic['name']}",
            ))
            used_minutes += duration

        for i, state in enumerate(due_states):
            duration = _duration_for_confidence(state.last_confidence)
            if used_minutes + duration > budget_minutes:
                break
            day = remaining_days[i % len(remaining_days)]
            concept = concepts_by_id.get(state.concept_id)
            blocks.append(ScheduleBlock(
                week_id=week.id, concept_id=state.concept_id, day=_day_datetime(day),
                duration_minutes=duration, block_type="review", status="planned",
                label=f"Spaced review: {concept.canonical_name if concept else state.concept_id}",
            ))
            used_minutes += duration

    db.add_all(blocks)
    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks
