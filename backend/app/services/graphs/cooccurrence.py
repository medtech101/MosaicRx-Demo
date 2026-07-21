"""
Builds the co-word network (the co-citation-analysis analog applied to a
personal study corpus instead of publication data): nodes are concepts,
edges are weighted by how often two concepts co-occur - within the same
slide/paragraph ("slide" scope, the tightest signal) and within the same
lecture more broadly ("lecture" scope, a weaker signal used to connect
material that never shares a single slide but clearly belongs to the same
talk).
"""
import itertools
from collections import Counter

from sqlalchemy.orm import Session

from app.models import Concept, ConceptOccurrence, ConceptEdge, Document
from app.services.nlp.concept_extractor import get_concept_extractor
from app.services.sanitize.pipeline import SanitizedUnit

MIN_CONCEPT_LEN = 3
CONTENT_KINDS = {"body", "notes"}


def _get_or_create_concept(db: Session, canonical_name: str) -> Concept:
    concept = db.query(Concept).filter(Concept.canonical_name == canonical_name).first()
    if concept is None:
        concept = Concept(canonical_name=canonical_name, aliases=[])
        db.add(concept)
        db.flush()
    return concept


def _upsert_edge(db: Session, concept_a_id: int, concept_b_id: int, scope: str, weight_delta: float) -> None:
    lo, hi = sorted((concept_a_id, concept_b_id))
    edge = (
        db.query(ConceptEdge)
        .filter(ConceptEdge.concept_a_id == lo, ConceptEdge.concept_b_id == hi, ConceptEdge.scope == scope)
        .first()
    )
    if edge:
        edge.weight += weight_delta
    else:
        db.add(ConceptEdge(concept_a_id=lo, concept_b_id=hi, scope=scope, weight=weight_delta))


def ingest_concepts_for_document(db: Session, document: Document, units: list[SanitizedUnit]) -> set[str]:
    """Extracts concepts from a document's sanitized units, upserts Concept /
    ConceptOccurrence / ConceptEdge rows. Must be called with the final
    sanitized text (post redaction-override) - never raw text - since this
    feeds the graph that every other module reads from. Returns the set of
    canonical concept names touched, for convenience."""
    extractor = get_concept_extractor()

    unit_concepts: list[set[str]] = []
    occurrence_locations: dict[str, list[str]] = {}

    for u in units:
        if u.kind not in CONTENT_KINDS:
            continue
        spans = extractor.extract(u.sanitized_text)
        names = {s.canonical for s in spans if len(s.canonical) >= MIN_CONCEPT_LEN}
        unit_concepts.append(names)
        for name in names:
            occurrence_locations.setdefault(name, []).append(u.location)

    all_names = set().union(*unit_concepts) if unit_concepts else set()
    if not all_names:
        return set()

    name_to_id: dict[str, int] = {}
    for name in all_names:
        concept = _get_or_create_concept(db, name)
        name_to_id[name] = concept.id
        for location in occurrence_locations.get(name, []):
            db.add(ConceptOccurrence(
                concept_id=concept.id, document_id=document.id,
                location=location, week_id=document.week_id,
            ))

    slide_pairs: Counter = Counter()
    for names in unit_concepts:
        for a, b in itertools.combinations(sorted(names), 2):
            slide_pairs[(a, b)] += 1

    lecture_pairs: Counter = Counter()
    for a, b in itertools.combinations(sorted(all_names), 2):
        lecture_pairs[(a, b)] += 1

    for (a, b), count in slide_pairs.items():
        _upsert_edge(db, name_to_id[a], name_to_id[b], "slide", float(count))
    for (a, b), count in lecture_pairs.items():
        # lecture-scope co-occurrence is the weaker signal; slide co-occurrence
        # for the same pair already carries the real weight in its own scope.
        _upsert_edge(db, name_to_id[a], name_to_id[b], "lecture", float(count))

    db.commit()
    return all_names
