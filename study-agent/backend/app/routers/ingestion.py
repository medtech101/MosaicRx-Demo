import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.config import UPLOADS_DIR
from app.database import get_db
from app.models import Document, RedactionEntry, ImageFlag, DocumentUnit
from app.schemas import DocumentOut
from app.services.sanitize.pipeline import run_ingestion_pipeline
from .settings import terms_by_category

router = APIRouter(prefix="/api/documents", tags=["ingestion"])

ALLOWED_EXTENSIONS = {"pptx", "pdf", "docx"}


def _images_dir(document_id: int) -> Path:
    d = UPLOADS_DIR / f"doc_{document_id}_images"
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '.{ext}'. Allowed: pptx, pdf, docx.")

    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = UPLOADS_DIR / stored_name
    with stored_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    doc = Document(
        original_filename=file.filename,
        doc_type=ext,
        status="processing",
        upload_path=str(stored_path),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        terms = terms_by_category(db)
        result = run_ingestion_pipeline(str(stored_path), ext, terms)
    except Exception as exc:
        doc.status = "error"
        db.commit()
        raise HTTPException(500, f"Failed to parse/sanitize document: {exc}")

    doc.unit_count = result.unit_count
    doc.sanitized_markdown = result.sanitized_markdown
    doc.status = "pending_review"

    for order_index, u in enumerate(result.units):
        db.add(DocumentUnit(
            document_id=doc.id, location=u.location, kind=u.kind,
            original_text=u.original_text, order_index=order_index,
        ))
        for r in u.redactions:
            db.add(RedactionEntry(
                document_id=doc.id, location=r.location, kind=r.kind, category=r.category,
                original_text=r.original, replacement_text=r.replacement, status="pending",
            ))
    for r in result.metadata_redactions:
        db.add(RedactionEntry(
            document_id=doc.id, location=r.location, kind="metadata", category=r.category,
            original_text=r.original, replacement_text=r.replacement, status="pending",
        ))

    images_dir = _images_dir(doc.id)
    for i, dec in enumerate(result.image_decisions):
        if not (dec.is_logo or dec.needs_review):
            continue  # clean content image - no action needed
        ext_img = dec.image.ext or "png"
        thumb_path = images_dir / f"{i}.{ext_img}"
        thumb_path.write_bytes(dec.image.data)
        db.add(ImageFlag(
            document_id=doc.id,
            location=dec.image.location,
            reason="logo_heuristic" if dec.is_logo else "ocr_blocklist_match",
            ocr_text=dec.ocr_text or None,
            matched_terms=dec.matched_terms or None,
            action="removed" if dec.is_logo else "pending",
            thumbnail_path=str(thumb_path),
            ext=ext_img,
        ))

    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()
