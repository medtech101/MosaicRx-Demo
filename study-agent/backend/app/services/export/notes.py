import io

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from sqlalchemy.orm import Session

from app.models import Document


def get_sanitized_markdown(db: Session, document_id: int) -> tuple[str, str]:
    """Returns (filename_stem, markdown). Raises if the document isn't
    confirmed - only sanitized, persisted content is ever exportable."""
    doc = db.get(Document, document_id)
    if not doc or doc.status != "confirmed" or not doc.sanitized_markdown:
        raise ValueError("Document not found or not yet confirmed/sanitized")
    stem = doc.original_filename.rsplit(".", 1)[0]
    return stem, doc.sanitized_markdown


def markdown_to_pdf_bytes(markdown_text: str, title: str) -> bytes:
    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER)
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.startswith("### "):
            story.append(Paragraph(escaped[4:], styles["Heading3"]))
        elif line.startswith("> "):
            story.append(Paragraph(f"<i>{escaped[2:]}</i>", styles["BodyText"]))
        else:
            story.append(Paragraph(escaped, styles["BodyText"]))

    doc.build(story)
    return buf.getvalue()
