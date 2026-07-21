"""
SM-2 spaced-repetition interval model (SuperMemo 2), applied per concept
cluster instead of per flashcard. A 1-4 confidence rating from the study
block feedback loop maps onto SM-2's 0-5 quality scale; low confidence
resets the interval and pulls the next review in immediately, high
confidence grows the interval and pushes it out - exactly the behavior
the spec asks for.
"""
import datetime as dt

from app.models import ConceptReviewState

MIN_EASE_FACTOR = 1.3

# 1 (no idea) -> quality 1 (near-total fail); 4 (nailed it) -> quality 5 (perfect)
CONFIDENCE_TO_QUALITY = {1: 1, 2: 3, 3: 4, 4: 5}


def apply_confidence_rating(state: ConceptReviewState, confidence: int) -> ConceptReviewState:
    quality = CONFIDENCE_TO_QUALITY[confidence]
    now = dt.datetime.utcnow()

    if quality < 3:
        state.repetitions = 0
        interval = 1.0
    else:
        if state.repetitions == 0:
            interval = 1.0
        elif state.repetitions == 1:
            interval = 6.0
        else:
            interval = round(state.interval_days * state.ease_factor, 1)
        state.repetitions += 1

    state.ease_factor = max(
        MIN_EASE_FACTOR,
        state.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )
    state.interval_days = interval
    state.due_date = now + dt.timedelta(days=interval)
    state.last_confidence = confidence
    state.last_reviewed_at = now
    return state


def get_or_create_review_state(db, concept_id: int) -> ConceptReviewState:
    state = db.query(ConceptReviewState).filter(ConceptReviewState.concept_id == concept_id).first()
    if state is None:
        state = ConceptReviewState(concept_id=concept_id)
        db.add(state)
        db.flush()
    return state
