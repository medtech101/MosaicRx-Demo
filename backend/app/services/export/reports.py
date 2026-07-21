from sqlalchemy.orm import Session

from app.models import Concept
from app.services.graphs.analysis import get_latest_snapshot, compute_and_store_snapshot


def bridge_concepts_report(db: Session) -> str:
    snapshot = get_latest_snapshot(db) or compute_and_store_snapshot(db)
    lines = ["# Bridge Concepts", "", (
        "Ranked by betweenness centrality - the concepts most likely to connect otherwise "
        "separate topics in your corpus."
    ), ""]
    if not snapshot.bridge_concepts:
        lines.append("_No bridge concepts yet - confirm more than one lecture to see cross-topic links._")
    else:
        for i, b in enumerate(snapshot.bridge_concepts, start=1):
            lines.append(f"{i}. **{b['name']}** - betweenness {b['betweenness']:.3f}")
    return "\n".join(lines) + "\n"


def cluster_summary_report(db: Session) -> str:
    snapshot = get_latest_snapshot(db) or compute_and_store_snapshot(db)
    concepts = {c.id: c for c in db.query(Concept).all()}

    clusters: dict[str, list[int]] = {}
    for cid_str, community_id in snapshot.communities.items():
        clusters.setdefault(str(community_id), []).append(int(cid_str))

    lines = ["# Cluster Summary", "", "Concept themes found via Louvain community detection.", ""]
    if not clusters:
        lines.append("_No clusters yet - confirm at least one lecture to build the graph._")
    for community_id, member_ids in sorted(clusters.items(), key=lambda kv: int(kv[0])):
        label = snapshot.community_labels.get(community_id, f"Cluster {community_id}")
        lines.append(f"## {label}")
        member_names = sorted(concepts[cid].canonical_name for cid in member_ids if cid in concepts)
        for name in member_names:
            lines.append(f"- {name}")
        lines.append("")
    return "\n".join(lines) + "\n"
