import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import SANITIZED_DIR
from app.database import get_db
from app.models import Document, RedactionEntry, ImageFlag, DocumentUnit
from app.schemas import DocumentReviewOut, ConfirmRequest
from app.services.sanitize.blocklist import find_blocklist_matches
from app.services.sanitize.image_scrub import strip_exif
from app.services.sanitize.pipeline import build_markdown, SanitizedUnit
from .settings import terms_by_category

router = APIRouter(prefix="/api/documents", tags=["review"])


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/{document_id}/review", response_model=DocumentReviewOut)
def get_review(document_id: int, db: Session = Depends(get_db)):
    doc = _get_document_or_404(document_id, db)
    if doc.status not in ("pending_review",):
        raise HTTPException(400, f"Document is '{doc.status}', not awaiting review")

    redactions = db.query(RedactionEntry).filter(RedactionEntry.document_id == document_id).all()
    image_flags = db.query(ImageFlag).filter(ImageFlag.document_id == document_id).all()

    preview = doc.sanitized_markdown or ""
    return DocumentReviewOut(
        document=doc,
        redactions=redactions,
        image_flags=image_flags,
        sanitized_markdown_preview=preview[:4000],
    )


def _rebuild_units(document_id: int, db: Session, decisions: dict[int, bool]) -> list[SanitizedUnit]:
    """Reconstruct sanitized text per unit, honoring per-redaction approve/reject overrides.
    approve=True (default) -> keep the redaction; approve=False -> restore original text."""
    units = (
        db.query(DocumentUnit)
        .filter(DocumentUnit.document_id == document_id)
        .order_by(DocumentUnit.order_index)
        .all()
    )
    redactions = db.query(RedactionEntry).filter(RedactionEntry.document_id == document_id).all()
    by_location: dict[tuple[str, str], list[RedactionEntry]] = {}
    for r in redactions:
        if r.category == "metadata":
            continue
        by_location.setdefault((r.location, r.kind or ""), []).append(r)

    out = []
    for u in units:
        text = u.original_text
        for r in by_location.get((u.location, u.kind), []):
            approve = decisions.get(r.id, r.status != "rejected")
            if approve and r.original_text in text:
                text = text.replace(r.original_text, r.replacement_text)
        out.append(SanitizedUnit(location=u.location, kind=u.kind, original_text=u.original_text, sanitized_text=text))
    return out


@router.post("/{document_id}/confirm")
def confirm_document(document_id: int, payload: ConfirmRequest, db: Session = Depends(get_db)):
    doc = _get_document_or_404(document_id, db)
    if doc.status != "pending_review":
        raise HTTPException(400, f"Document is '{doc.status}', cannot confirm")

    redaction_decisions = {d.id: d.approve for d in payload.redaction_decisions}
    for r in db.query(RedactionEntry).filter(RedactionEntry.document_id == document_id).all():
        if r.id in redaction_decisions:
            r.status = "approved" if redaction_decisions[r.id] else "rejected"
        elif r.status == "pending":
            r.status = "approved"

    image_decisions = {d.id: d.action for d in payload.image_decisions}
    doc_dir = SANITIZED_DIR / str(document_id)
    images_out_dir = doc_dir / "images"
    kept_images = []
    for flag in db.query(ImageFlag).filter(ImageFlag.document_id == document_id).all():
        action = image_decisions.get(flag.id, flag.action if flag.action != "pending" else "removed")
        flag.action = action
        if action == "kept" and flag.thumbnail_path and Path(flag.thumbnail_path).exists():
            images_out_dir.mkdir(parents=True, exist_ok=True)
            data = Path(flag.thumbnail_path).read_bytes()
            clean = strip_exif(data)
            out_path = images_out_dir / f"{flag.id}.{flag.ext or 'png'}"
            out_path.write_bytes(clean)
            kept_images.append((flag.location, out_path))

    rebuilt_units = _rebuild_units(document_id, db, redaction_decisions)
    markdown = build_markdown(rebuilt_units)
    if kept_images:
        image_lines = "\n".join(f"- retained image at {loc}: images/{p.name}" for loc, p in kept_images)
        markdown += f"\n\n### Retained images\n{image_lines}\n"

    # Final blocklist safety-net scan before anything is persisted long-term.
    terms = terms_by_category(db)
    leftover = find_blocklist_matches(markdown, terms)
    if leftover:
        raise HTTPException(
            422,
            f"Final blocklist scan found {len(leftover)} unresolved term(s) "
            f"(e.g. '{leftover[0].original}'). Resolve these redactions before confirming.",
        )

    doc_dir.mkdir(parents=True, exist_ok=True)
    md_path = doc_dir / "notes.md"
    md_path.write_text(markdown, encoding="utf-8")

    # Original upload is deleted immediately once sanitization is confirmed - only the
    # sanitized version persists from this point on.
    if doc.upload_path and Path(doc.upload_path).exists():
        Path(doc.upload_path).unlink()
    images_tmp_dir = Path(doc.upload_path).parent / f"doc_{document_id}_images" if doc.upload_path else None
    if images_tmp_dir and images_tmp_dir.exists():
        shutil.rmtree(images_tmp_dir, ignore_errors=True)

    db.query(DocumentUnit).filter(DocumentUnit.document_id == document_id).delete()

    doc.status = "confirmed"
    doc.upload_path = None
    doc.sanitized_path = str(md_path)
    doc.sanitized_markdown = markdown
    from datetime import datetime
    doc.confirmed_at = datetime.utcnow()

    db.commit()
    return {"ok": True, "sanitized_path": str(md_path)}


@router.post("/{document_id}/reject")
def reject_document(document_id: int, db: Session = Depends(get_db)):
    doc = _get_document_or_404(document_id, db)
    if doc.upload_path and Path(doc.upload_path).exists():
        Path(doc.upload_path).unlink()
    images_tmp_dir = Path(doc.upload_path).parent / f"doc_{document_id}_images" if doc.upload_path else None
    if images_tmp_dir and images_tmp_dir.exists():
        shutil.rmtree(images_tmp_dir, ignore_errors=True)
    db.delete(doc)
    db.commit()
    return {"ok": True}
