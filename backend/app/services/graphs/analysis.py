"""
Bibliometric-style network analysis over the concept co-word graph:
  - betweenness centrality to surface "bridge concepts" - the high-yield
    integrative nodes connecting otherwise-separate clusters (the classic
    co-citation-mapping technique, applied here to a personal study corpus).
  - Louvain community detection to group concepts into themes for the
    cluster map.
Runs on the cumulative graph built from every confirmed document to date,
so the "big picture" always reflects the whole corpus, not just one week.
"""
import datetime as dt

import networkx as nx
from sqlalchemy.orm import Session

from app.models import Concept, ConceptEdge, GraphSnapshot

LECTURE_SCOPE_WEIGHT = 0.3  # lecture-level co-occurrence is a weaker signal than same-slide


def build_networkx_graph(db: Session) -> nx.Graph:
    graph = nx.Graph()
    concepts = db.query(Concept).all()
    for c in concepts:
        graph.add_node(c.id, name=c.canonical_name)

    combined: dict[tuple[int, int], float] = {}
    for edge in db.query(ConceptEdge).all():
        key = (edge.concept_a_id, edge.concept_b_id)
        factor = 1.0 if edge.scope == "slide" else LECTURE_SCOPE_WEIGHT
        combined[key] = combined.get(key, 0.0) + edge.weight * factor

    for (a, b), weight in combined.items():
        if weight > 0:
            graph.add_edge(a, b, weight=weight)

    return graph


def compute_and_store_snapshot(db: Session, new_week_id: int | None = None) -> GraphSnapshot:
    graph = build_networkx_graph(db)

    bridge_concepts: list[dict] = []
    communities: dict[str, int] = {}
    community_labels: dict[str, str] = {}

    if graph.number_of_nodes() > 0:
        betweenness = nx.betweenness_centrality(graph, weight=None, normalized=True) if graph.number_of_edges() > 0 else {
            n: 0.0 for n in graph.nodes
        }
        id_to_name = {n: graph.nodes[n]["name"] for n in graph.nodes}
        ranked = sorted(betweenness.items(), key=lambda kv: kv[1], reverse=True)
        bridge_concepts = [
            {"concept_id": nid, "name": id_to_name[nid], "betweenness": round(score, 4)}
            for nid, score in ranked
            if score > 0
        ][:25]

        if graph.number_of_edges() > 0:
            found = nx.algorithms.community.louvain_communities(graph, weight="weight", seed=42)
        else:
            found = [{n} for n in graph.nodes]

        for community_id, members in enumerate(found):
            member_names = [id_to_name[m] for m in members]
            # label a cluster by its highest-betweenness (most "central") member
            label_member = max(members, key=lambda m: betweenness.get(m, 0.0))
            community_labels[str(community_id)] = id_to_name[label_member]
            for m in members:
                communities[str(m)] = community_id

    snapshot = GraphSnapshot(
        computed_at=dt.datetime.utcnow(),
        bridge_concepts=bridge_concepts,
        communities=communities,
        community_labels=community_labels,
        new_week_id=new_week_id,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_latest_snapshot(db: Session) -> GraphSnapshot | None:
    return db.query(GraphSnapshot).order_by(GraphSnapshot.computed_at.desc()).first()
