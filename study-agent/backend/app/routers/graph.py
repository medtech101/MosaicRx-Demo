from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Concept, ConceptEdge, ConceptOccurrence, Document
from app.services.graphs.analysis import build_networkx_graph, compute_and_store_snapshot, get_latest_snapshot

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("")
def get_graph(db: Session = Depends(get_db)):
    snapshot = get_latest_snapshot(db)
    if snapshot is None:
        snapshot = compute_and_store_snapshot(db)

    graph = build_networkx_graph(db)
    concepts = {c.id: c for c in db.query(Concept).all()}

    nodes = [
        {
            "id": cid,
            "name": concepts[cid].canonical_name,
            "degree": graph.degree(cid, weight="weight") if cid in graph else 0,
            "betweenness": next(
                (b["betweenness"] for b in snapshot.bridge_concepts if b["concept_id"] == cid), 0.0
            ),
            "community": snapshot.communities.get(str(cid)),
        }
        for cid in concepts
    ]
    edges = [
        {"source": u, "target": v, "weight": round(data["weight"], 2)}
        for u, v, data in graph.edges(data=True)
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "bridge_concepts": snapshot.bridge_concepts,
        "community_labels": snapshot.community_labels,
        "computed_at": snapshot.computed_at,
    }


@router.post("/recompute")
def recompute_graph(db: Session = Depends(get_db)):
    snapshot = compute_and_store_snapshot(db)
    return {"ok": True, "computed_at": snapshot.computed_at, "bridge_concepts": snapshot.bridge_concepts}


@router.get("/concepts/{concept_id}")
def get_concept_detail(concept_id: int, db: Session = Depends(get_db)):
    concept = db.get(Concept, concept_id)
    if not concept:
        raise HTTPException(404, "Concept not found")

    occurrences = (
        db.query(ConceptOccurrence, Document)
        .join(Document, ConceptOccurrence.document_id == Document.id)
        .filter(ConceptOccurrence.concept_id == concept_id)
        .all()
    )
    edges = (
        db.query(ConceptEdge)
        .filter((ConceptEdge.concept_a_id == concept_id) | (ConceptEdge.concept_b_id == concept_id))
        .all()
    )
    related_ids = {e.concept_a_id if e.concept_a_id != concept_id else e.concept_b_id for e in edges}
    related = db.query(Concept).filter(Concept.id.in_(related_ids)).all() if related_ids else []

    return {
        "concept": {"id": concept.id, "canonical_name": concept.canonical_name, "aliases": concept.aliases},
        "occurrences": [
            {"document_id": d.id, "filename": d.original_filename, "location": occ.location}
            for occ, d in occurrences
        ],
        "related_concepts": [{"id": r.id, "name": r.canonical_name} for r in related],
    }
