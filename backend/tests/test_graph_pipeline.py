"""
Verifies Module 2's co-word graph: concept extraction across three synthetic
"lectures" (renal, cardiovascular, pharmacology) that share the
renin-angiotensin system / hypertension concepts, exactly the cross-system
bridging scenario called out in the spec. Asserts betweenness centrality
correctly surfaces the shared concepts as bridges and Louvain finds at least
two distinct clusters.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models  # noqa: F401 - registers all tables on Base
from app.models import Document
from app.services.graphs.cooccurrence import ingest_concepts_for_document
from app.services.graphs.analysis import compute_and_store_snapshot, build_networkx_graph
from app.services.sanitize.pipeline import SanitizedUnit


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _units(*texts: str) -> list[SanitizedUnit]:
    return [
        SanitizedUnit(location=f"slide {i+1}", kind="body", original_text=t, sanitized_text=t)
        for i, t in enumerate(texts)
    ]


def _make_document(db_session, filename: str) -> Document:
    doc = Document(original_filename=filename, doc_type="pptx", status="pending_review")
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


RENAL_SLIDES = _units(
    "The kidney regulates fluid balance via the nephron and glomerular filtration rate.",
    "Chronic kidney disease often stems from long-standing hypertension damaging the nephron.",
    "The renin-angiotensin system is central to renal blood pressure regulation, along with aldosterone.",
)
CARDIO_SLIDES = _units(
    "Heart failure reduces cardiac output and can result from chronic hypertension.",
    "Myocardial infarction and atherosclerosis are major causes of heart failure.",
    "The renin-angiotensin system also plays a key role in heart failure progression.",
)
PHARM_SLIDES = _units(
    "ACE inhibitors block the renin-angiotensin system to treat hypertension.",
    "Beta blockers and calcium channel blockers are alternative antihypertensives.",
    "Pharmacokinetics determines how the ace inhibitor dose is adjusted in renal disease.",
)


@pytest.fixture
def seeded_graph(db_session):
    for filename, units in [
        ("renal_lecture.pptx", RENAL_SLIDES),
        ("cardio_lecture.pptx", CARDIO_SLIDES),
        ("pharm_lecture.pptx", PHARM_SLIDES),
    ]:
        doc = _make_document(db_session, filename)
        ingest_concepts_for_document(db_session, doc, units)
    snapshot = compute_and_store_snapshot(db_session)
    return db_session, snapshot


def test_concepts_and_edges_created(seeded_graph):
    db_session, _ = seeded_graph
    graph = build_networkx_graph(db_session)
    assert graph.number_of_nodes() >= 8
    assert graph.number_of_edges() > 0


def test_bridge_concepts_surface_cross_system_terms(seeded_graph):
    _, snapshot = seeded_graph
    bridge_names = {b["name"] for b in snapshot.bridge_concepts}
    # renin-angiotensin system and/or hypertension must appear near the top -
    # they are the only concepts shared across all three "lectures".
    top_5 = {b["name"] for b in snapshot.bridge_concepts[:5]}
    assert bridge_names & {"renin-angiotensin system", "hypertension"}
    assert top_5 & {"renin-angiotensin system", "hypertension"}


def test_louvain_finds_multiple_clusters(seeded_graph):
    _, snapshot = seeded_graph
    community_ids = set(snapshot.communities.values())
    assert len(community_ids) >= 2
