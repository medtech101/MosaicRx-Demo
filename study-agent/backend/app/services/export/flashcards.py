"""
Generates Anki-compatible flashcards from extracted concepts and their
co-occurrence relationships. Prefers the configured LLM (sanitized-content-
only, enforced in app.services.llm.client) for higher-quality cards; falls
back to a deterministic template when no LLM_API_KEY is configured so the
export center never depends on one being set up.
"""
import csv
import io

from sqlalchemy.orm import Session

from app.models import Concept, ConceptEdge, ConceptOccurrence, Document
from app.services.llm.client import call_llm

SYSTEM_PROMPT = (
    "You write concise, high-yield medical-school flashcards from a list of concepts and how "
    "they relate to each other. Given ONE concept and its related concepts, output exactly one "
    "flashcard as two lines: 'Front: <question>' then 'Back: <answer>'. Keep the answer under "
    "40 words. Do not include any other text."
)


def _related_concept_names(db: Session, concept_id: int, limit: int = 4) -> list[str]:
    edges = (
        db.query(ConceptEdge)
        .filter((ConceptEdge.concept_a_id == concept_id) | (ConceptEdge.concept_b_id == concept_id))
        .order_by(ConceptEdge.weight.desc())
        .limit(limit)
        .all()
    )
    related_ids = [e.concept_b_id if e.concept_a_id == concept_id else e.concept_a_id for e in edges]
    if not related_ids:
        return []
    rows = db.query(Concept).filter(Concept.id.in_(related_ids)).all()
    return [r.canonical_name for r in rows]


def _source_lecture_names(db: Session, concept_id: int) -> list[str]:
    rows = (
        db.query(Document.original_filename)
        .join(ConceptOccurrence, ConceptOccurrence.document_id == Document.id)
        .filter(ConceptOccurrence.concept_id == concept_id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def _fallback_card(concept_name: str, related: list[str], sources: list[str]) -> tuple[str, str]:
    front = f"What is {concept_name}, and what does it connect to?"
    relates_to = f" It relates to {', '.join(related)}." if related else ""
    from_lectures = f" Covered in: {', '.join(sources)}." if sources else ""
    back = f"A concept from your notes.{relates_to}{from_lectures}".strip()
    return front, back


def _parse_llm_card(text: str, concept_name: str, related: list[str], sources: list[str]) -> tuple[str, str]:
    front, back = None, None
    for line in text.splitlines():
        if line.strip().lower().startswith("front:"):
            front = line.split(":", 1)[1].strip()
        elif line.strip().lower().startswith("back:"):
            back = line.split(":", 1)[1].strip()
    if not front or not back:
        return _fallback_card(concept_name, related, sources)
    return front, back


def generate_flashcards(db: Session) -> list[dict]:
    concepts = db.query(Concept).all()
    cards = []
    for concept in concepts:
        related = _related_concept_names(db, concept.id)
        sources = _source_lecture_names(db, concept.id)

        user_prompt = (
            f"Concept: {concept.canonical_name}\n"
            f"Related concepts: {', '.join(related) if related else '(none yet)'}\n"
            f"Covered in lectures: {', '.join(sources) if sources else '(unknown)'}"
        )
        llm_response = call_llm(db, SYSTEM_PROMPT, user_prompt, sanitized_sources=[user_prompt])

        if llm_response:
            front, back = _parse_llm_card(llm_response, concept.canonical_name, related, sources)
        else:
            front, back = _fallback_card(concept.canonical_name, related, sources)

        cards.append({"concept_id": concept.id, "front": front, "back": back})
    return cards


def flashcards_to_anki_csv(cards: list[dict]) -> str:
    """Plain two-column CSV (Front,Back), no header row - Anki's basic CSV
    importer maps the first two columns to the Basic note type by default."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for card in cards:
        writer.writerow([card["front"], card["back"]])
    return buf.getvalue()
