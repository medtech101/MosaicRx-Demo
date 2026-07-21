"""
Exports the cumulative knowledge graph in three forms: GraphML (for Gephi/
Cytoscape), plain JSON (for anything else), and a high-resolution PNG
snapshot colored by Louvain community - the same layout logic as the
in-app force-directed graph, just rendered server-side with matplotlib.
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from sqlalchemy.orm import Session

from app.models import Concept
from app.services.graphs.analysis import build_networkx_graph, get_latest_snapshot, compute_and_store_snapshot

COMMUNITY_COLORS = [
    "#5b8cff", "#ff8a5b", "#35c46f", "#e35bff", "#ffcf6b",
    "#5bd8ff", "#ff5b6a", "#a4ff5b", "#c45bff", "#5bffb0",
]


def export_graphml(db: Session) -> str:
    graph = build_networkx_graph(db)
    buf = io.BytesIO()
    nx.write_graphml(graph, buf)
    return buf.getvalue().decode("utf-8")


def export_graph_json(db: Session) -> dict:
    snapshot = get_latest_snapshot(db) or compute_and_store_snapshot(db)
    graph = build_networkx_graph(db)
    concepts = {c.id: c for c in db.query(Concept).all()}

    nodes = [
        {
            "id": cid,
            "name": concepts[cid].canonical_name,
            "degree": graph.degree(cid, weight="weight") if cid in graph else 0,
            "betweenness": next((b["betweenness"] for b in snapshot.bridge_concepts if b["concept_id"] == cid), 0.0),
            "community": snapshot.communities.get(str(cid)),
        }
        for cid in concepts
    ]
    edges = [{"source": u, "target": v, "weight": round(d["weight"], 2)} for u, v, d in graph.edges(data=True)]
    return {
        "nodes": nodes, "edges": edges,
        "bridge_concepts": snapshot.bridge_concepts,
        "community_labels": snapshot.community_labels,
        "computed_at": snapshot.computed_at.isoformat(),
    }


def export_graph_png(db: Session) -> bytes:
    snapshot = get_latest_snapshot(db) or compute_and_store_snapshot(db)
    graph = build_networkx_graph(db)
    concepts = {c.id: c for c in db.query(Concept).all()}

    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    if graph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No concepts yet", ha="center", va="center")
        ax.axis("off")
    else:
        pos = nx.spring_layout(graph, seed=42, weight="weight")
        colors = [
            COMMUNITY_COLORS[snapshot.communities.get(str(n), 0) % len(COMMUNITY_COLORS)]
            for n in graph.nodes
        ]
        sizes = [200 + 40 * graph.degree(n, weight="weight") for n in graph.nodes]
        nx.draw_networkx_edges(graph, pos, ax=ax, alpha=0.25, width=1)
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=colors, node_size=sizes)
        labels = {n: concepts[n].canonical_name for n in graph.nodes}
        nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=8)
        ax.axis("off")
        ax.set_title("Personal study knowledge graph", fontsize=14)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()
