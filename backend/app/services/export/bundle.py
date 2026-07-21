"""
The single export center: packages sanitized notes, the knowledge graph,
bridge/cluster reports, flashcards, schedules, and resource ratings -
individually or as one ZIP. Every piece of text content is re-scanned
against the live blocklist before it's allowed into the bundle; a single
leftover match anywhere fails the whole export rather than silently
shipping a partial, unverified bundle.
"""
import json
import zipfile
from dataclasses import dataclass
from io import BytesIO

from sqlalchemy.orm import Session

from app.models import Document
from app.routers.settings import terms_by_category
from app.services.sanitize.blocklist import find_blocklist_matches
from app.services.export.notes import get_sanitized_markdown, markdown_to_pdf_bytes
from app.services.export.graph_export import export_graphml, export_graph_json, export_graph_png
from app.services.export.reports import bridge_concepts_report, cluster_summary_report
from app.services.export.flashcards import generate_flashcards, flashcards_to_anki_csv
from app.services.export.tabular import schedule_to_csv, resource_ratings_to_csv
from app.services.scheduler.ics_export import export_week_ics, scannable_ics_text


@dataclass
class BlocklistViolation:
    artifact: str
    term: str


def scan_text_or_raise(terms: dict[str, list[str]], artifact: str, text: str, violations: list[BlocklistViolation]) -> None:
    for match in find_blocklist_matches(text, terms):
        violations.append(BlocklistViolation(artifact=artifact, term=match.original))


def build_export_bundle(db: Session) -> bytes:
    terms = terms_by_category(db)
    violations: list[BlocklistViolation] = []

    text_artifacts: dict[str, str] = {}

    confirmed_docs = db.query(Document).filter(Document.status == "confirmed").all()
    for doc in confirmed_docs:
        stem, markdown = get_sanitized_markdown(db, doc.id)
        text_artifacts[f"notes/{stem}.md"] = markdown

    bridge_md = bridge_concepts_report(db)
    cluster_md = cluster_summary_report(db)
    text_artifacts["reports/bridge_concepts.md"] = bridge_md
    text_artifacts["reports/cluster_summary.md"] = cluster_md

    cards = generate_flashcards(db)
    flashcards_csv = flashcards_to_anki_csv(cards)
    text_artifacts["flashcards/flashcards.csv"] = flashcards_csv

    schedule_csv = schedule_to_csv(db)
    schedule_ics = export_week_ics(db)
    text_artifacts["schedule/schedule.csv"] = schedule_csv
    text_artifacts["schedule/schedule.ics"] = schedule_ics

    resource_ratings_csv = resource_ratings_to_csv(db)
    text_artifacts["resources/resource_ratings.csv"] = resource_ratings_csv

    graph_json = json.dumps(export_graph_json(db), indent=2, default=str)
    text_artifacts["graph/graph.json"] = graph_json

    graphml = export_graphml(db)
    text_artifacts["graph/graph.graphml"] = graphml

    # What actually gets scanned per artifact - identical to what's written,
    # except the .ics file where library-generated UID/DTSTAMP lines (not
    # user content) are stripped first to avoid a false-positive match.
    scan_targets = dict(text_artifacts)
    scan_targets["schedule/schedule.ics"] = scannable_ics_text(schedule_ics)

    for artifact_name, text in scan_targets.items():
        scan_text_or_raise(terms, artifact_name, text, violations)

    if violations:
        details = "; ".join(f"{v.artifact}: '{v.term}'" for v in violations[:5])
        raise ValueError(
            f"Final blocklist scan found {len(violations)} unresolved term(s) before export - "
            f"refusing to build the bundle. {details}"
        )

    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for artifact_name, text in text_artifacts.items():
            zf.writestr(artifact_name, text)

        for doc in confirmed_docs:
            stem, markdown = get_sanitized_markdown(db, doc.id)
            pdf_bytes = markdown_to_pdf_bytes(markdown, doc.original_filename)
            zf.writestr(f"notes/{stem}.pdf", pdf_bytes)

        zf.writestr("graph/graph.png", export_graph_png(db))

    return zip_buf.getvalue()
