from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.sanitize.blocklist import find_blocklist_matches
from app.services.export.notes import get_sanitized_markdown, markdown_to_pdf_bytes
from app.services.export.graph_export import export_graphml, export_graph_json, export_graph_png
from app.services.export.reports import bridge_concepts_report, cluster_summary_report
from app.services.export.flashcards import generate_flashcards, flashcards_to_anki_csv
from app.services.export.tabular import schedule_to_csv, resource_ratings_to_csv
from app.services.export.bundle import build_export_bundle
from app.services.scheduler.ics_export import export_week_ics, scannable_ics_text
from .settings import terms_by_category

router = APIRouter(prefix="/api/export", tags=["export"])


def _scan_or_422(db: Session, artifact: str, text: str) -> None:
    terms = terms_by_category(db)
    matches = find_blocklist_matches(text, terms)
    if matches:
        raise HTTPException(
            422,
            f"Final blocklist scan found an unresolved term in {artifact}: '{matches[0].original}'. "
            f"Refusing to export.",
        )


def _download(content: str | bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/notes/{document_id}/markdown")
def export_notes_markdown(document_id: int, db: Session = Depends(get_db)):
    try:
        stem, markdown = get_sanitized_markdown(db, document_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    _scan_or_422(db, f"{stem}.md", markdown)
    return _download(markdown, f"{stem}.md", "text/markdown")


@router.get("/notes/{document_id}/pdf")
def export_notes_pdf(document_id: int, db: Session = Depends(get_db)):
    try:
        stem, markdown = get_sanitized_markdown(db, document_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    _scan_or_422(db, f"{stem}.pdf", markdown)
    pdf_bytes = markdown_to_pdf_bytes(markdown, stem)
    return _download(pdf_bytes, f"{stem}.pdf", "application/pdf")


@router.get("/graph/graphml")
def export_graph_graphml_route(db: Session = Depends(get_db)):
    graphml = export_graphml(db)
    _scan_or_422(db, "graph.graphml", graphml)
    return _download(graphml, "graph.graphml", "application/xml")


@router.get("/graph/json")
def export_graph_json_route(db: Session = Depends(get_db)):
    payload = export_graph_json(db)
    _scan_or_422(db, "graph.json", str(payload))
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": 'attachment; filename="graph.json"'},
    )


@router.get("/graph/png")
def export_graph_png_route(db: Session = Depends(get_db)):
    png_bytes = export_graph_png(db)
    return _download(png_bytes, "graph.png", "image/png")


@router.get("/reports/bridge-concepts")
def export_bridge_concepts_route(db: Session = Depends(get_db)):
    report = bridge_concepts_report(db)
    _scan_or_422(db, "bridge_concepts.md", report)
    return _download(report, "bridge_concepts.md", "text/markdown")


@router.get("/reports/cluster-summary")
def export_cluster_summary_route(db: Session = Depends(get_db)):
    report = cluster_summary_report(db)
    _scan_or_422(db, "cluster_summary.md", report)
    return _download(report, "cluster_summary.md", "text/markdown")


@router.get("/flashcards.csv")
def export_flashcards_route(db: Session = Depends(get_db)):
    cards = generate_flashcards(db)
    csv_text = flashcards_to_anki_csv(cards)
    _scan_or_422(db, "flashcards.csv", csv_text)
    return _download(csv_text, "flashcards.csv", "text/csv")


@router.get("/schedule.csv")
def export_schedule_csv_route(db: Session = Depends(get_db)):
    csv_text = schedule_to_csv(db)
    _scan_or_422(db, "schedule.csv", csv_text)
    return _download(csv_text, "schedule.csv", "text/csv")


@router.get("/schedule.ics")
def export_schedule_ics_route(db: Session = Depends(get_db)):
    ics_text = export_week_ics(db)
    _scan_or_422(db, "schedule.ics", scannable_ics_text(ics_text))
    return _download(ics_text, "schedule.ics", "text/calendar")


@router.get("/resource-ratings.csv")
def export_resource_ratings_route(db: Session = Depends(get_db)):
    csv_text = resource_ratings_to_csv(db)
    _scan_or_422(db, "resource_ratings.csv", csv_text)
    return _download(csv_text, "resource_ratings.csv", "text/csv")


@router.get("/bundle.zip")
def export_bundle_route(db: Session = Depends(get_db)):
    try:
        zip_bytes = build_export_bundle(db)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return _download(zip_bytes, "study-agent-export.zip", "application/zip")
