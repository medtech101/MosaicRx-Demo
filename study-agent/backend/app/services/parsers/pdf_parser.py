import hashlib
import pdfplumber
from pypdf import PdfReader

from .base import ParsedDocument, TextUnit, ExtractedImage

META_MAP = {
    "/Author": "author",
    "/Company": "company",
    "/LastModifiedBy": "last_modified_by",
    "/Creator": "creator",
    "/Producer": "producer",
    "/Subject": "subject",
    "/Title": "title",
    "/Keywords": "keywords",
}


def parse_pdf(path: str) -> ParsedDocument:
    reader = PdfReader(path)
    doc = ParsedDocument(doc_type="pdf", unit_count=len(reader.pages))

    if reader.metadata:
        for pdf_key, out_key in META_MAP.items():
            value = reader.metadata.get(pdf_key)
            if value:
                doc.core_properties[out_key] = str(value)

    for page_idx, page in enumerate(reader.pages, start=1):
        try:
            for img in page.images:
                data = img.data
                doc.images.append(
                    ExtractedImage(
                        location=f"page {page_idx}",
                        source="content",
                        data=data,
                        ext="png",
                        occurrence_hash=hashlib.sha256(data).hexdigest(),
                    )
                )
        except Exception:
            pass

    with pdfplumber.open(path) as pl:
        for page_idx, page in enumerate(pl.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                doc.text_units.append(TextUnit(location=f"page {page_idx}", kind="body", text=text))

    return doc
