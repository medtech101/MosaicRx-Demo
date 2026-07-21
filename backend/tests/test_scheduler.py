import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Concept, ConceptOccurrence, ConceptReviewState, Week, AppSettingKV
from app.services.scheduler.week_detector import get_or_create_current_week
from app.services.scheduler.sm2 import get_or_create_review_state, apply_confidence_rating
from app.services.scheduler.plan_generator import generate_schedule
from app.models import Document


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test_api.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c, TestSession
    app.dependency_overrides.clear()


def test_current_week_is_monday_to_sunday(db_session):
    reference = dt.date(2026, 7, 22)  # a Wednesday
    week = get_or_create_current_week(db_session, reference)
    assert week.start_date.date() == dt.date(2026, 7, 20)  # Monday
    assert week.end_date.date() == dt.date(2026, 7, 26)  # Sunday

    same_week = get_or_create_current_week(db_session, dt.date(2026, 7, 24))
    assert same_week.id == week.id  # doesn't create a duplicate for the same week


def test_sm2_low_confidence_resets_and_pulls_review_earlier(db_session):
    concept = Concept(canonical_name="hypertension")
    db_session.add(concept)
    db_session.commit()

    state = get_or_create_review_state(db_session, concept.id)
    apply_confidence_rating(state, 4)  # ace it (rep 0 -> 1, interval 1 day)
    apply_confidence_rating(state, 4)  # ace it again (rep 1 -> 2, interval jumps to 6 days)
    long_interval = state.interval_days
    assert long_interval > 1.0

    apply_confidence_rating(state, 1)  # then bomb it
    assert state.repetitions == 0
    assert state.interval_days == 1.0
    assert state.interval_days < long_interval


def test_sm2_high_confidence_grows_interval(db_session):
    concept = Concept(canonical_name="nephron")
    db_session.add(concept)
    db_session.commit()

    state = get_or_create_review_state(db_session, concept.id)
    apply_confidence_rating(state, 4)
    first_interval = state.interval_days
    apply_confidence_rating(state, 4)
    second_interval = state.interval_days
    assert second_interval > first_interval


def test_generate_schedule_front_loads_new_and_interleaves_review(db_session):
    week = get_or_create_current_week(db_session)

    doc = Document(original_filename="week.pptx", doc_type="pptx", status="confirmed", week_id=week.id)
    db_session.add(doc)
    db_session.commit()

    new_concept = Concept(canonical_name="new topic")
    old_concept = Concept(canonical_name="old topic due for review")
    db_session.add_all([new_concept, old_concept])
    db_session.commit()

    db_session.add(ConceptOccurrence(concept_id=new_concept.id, document_id=doc.id, location="slide 1", week_id=week.id))
    db_session.commit()

    old_state = ConceptReviewState(
        concept_id=old_concept.id, due_date=dt.datetime.utcnow(), interval_days=3, ease_factor=2.3, repetitions=1,
    )
    db_session.add(old_state)
    db_session.add(AppSettingKV(key="weekly_hours", value=10))
    db_session.commit()

    blocks = generate_schedule(db_session, week)
    block_types = {b.block_type for b in blocks}
    assert "new" in block_types
    assert "review" in block_types
    assert any(b.concept_id == new_concept.id and b.block_type == "new" for b in blocks)
    assert any(b.concept_id == old_concept.id and b.block_type == "review" for b in blocks)


def test_generate_schedule_enters_taper_mode_near_exam(db_session):
    week = get_or_create_current_week(db_session)
    concept = Concept(canonical_name="taper concept")
    db_session.add(concept)
    db_session.commit()
    db_session.add(ConceptReviewState(concept_id=concept.id, due_date=dt.datetime.utcnow() + dt.timedelta(days=30)))
    exam_date = (dt.date.today() + dt.timedelta(days=3)).isoformat()
    db_session.add(AppSettingKV(key="exam_date", value=exam_date))
    db_session.add(AppSettingKV(key="weekly_hours", value=10))
    db_session.commit()

    blocks = generate_schedule(db_session, week)
    assert any(b.block_type == "taper" for b in blocks)


def test_regenerate_preserves_completed_blocks(db_session):
    week = get_or_create_current_week(db_session)
    concept = Concept(canonical_name="preserved concept")
    db_session.add(concept)
    db_session.commit()
    db_session.add(ConceptReviewState(concept_id=concept.id, due_date=dt.datetime.utcnow()))
    db_session.add(AppSettingKV(key="weekly_hours", value=10))
    db_session.commit()

    first_blocks = generate_schedule(db_session, week)
    first_blocks[0].status = "completed"
    first_blocks[0].confidence_rating = 3
    db_session.commit()
    completed_id = first_blocks[0].id

    generate_schedule(db_session, week)  # regenerate, e.g. after a mid-week upload

    from app.models import ScheduleBlock
    still_there = db_session.get(ScheduleBlock, completed_id)
    assert still_there is not None
    assert still_there.status == "completed"


def test_confidence_endpoint_updates_review_state(client):
    http_client, session_factory = client
    db = session_factory()
    week = get_or_create_current_week(db)
    concept = Concept(canonical_name="confidence concept")
    db.add(concept)
    db.commit()
    from app.models import ScheduleBlock
    block = ScheduleBlock(week_id=week.id, concept_id=concept.id, day=dt.datetime.utcnow(),
                          duration_minutes=25, block_type="new", status="planned", label="test block")
    db.add(block)
    db.commit()
    block_id = block.id
    db.close()

    resp = http_client.post(f"/api/scheduler/blocks/{block_id}/confidence", json={"rating": 2})
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["confidence_rating"] == 2


def test_ics_export_contains_events(client):
    http_client, session_factory = client
    db = session_factory()
    week = get_or_create_current_week(db)
    concept = Concept(canonical_name="ics concept")
    db.add(concept)
    db.commit()
    from app.models import ScheduleBlock
    db.add(ScheduleBlock(week_id=week.id, concept_id=concept.id, day=dt.datetime.utcnow(),
                          duration_minutes=30, block_type="new", status="planned", label="ICS test block"))
    db.commit()
    db.close()

    resp = http_client.get("/api/scheduler/export.ics")
    assert resp.status_code == 200
    assert "BEGIN:VCALENDAR" in resp.text
    assert "ICS test block" in resp.text
