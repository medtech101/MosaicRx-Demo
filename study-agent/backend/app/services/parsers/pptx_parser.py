import hashlib
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Length  # noqa: F401  (kept for future geometry heuristics)

from .base import ParsedDocument, TextUnit, ExtractedImage

CORE_PROP_FIELDS = [
    "author", "category", "comments", "content_status", "identifier",
    "keywords", "language", "last_modified_by", "subject", "title",
    "version", "revision",
]

FOOTER_PLACEHOLDER_IDX = {2, 12, 13}  # footer / slide number / date placeholder idx values (python-pptx PP_PLACEHOLDER)


def parse_pptx(path: str) -> ParsedDocument:
    prs = Presentation(path)
    doc = ParsedDocument(doc_type="pptx", unit_count=len(prs.slides))

    # --- core properties (author, company, last_modified_by, etc.) ---
    cp = prs.core_properties
    for field_name in CORE_PROP_FIELDS:
        value = getattr(cp, field_name, None)
        if value:
            doc.core_properties[field_name] = str(value)
    # python-pptx exposes "company" only via the underlying part properties in some versions
    try:
        company = cp._element.find(
            "{http://purl.org/dc/elements/1.1/}company"
        )
    except Exception:
        company = None
    if hasattr(cp, "company") and getattr(cp, "company"):
        doc.core_properties["company"] = str(cp.company)

    # --- slide master / layout footers (leak institutional identity even if body text is clean) ---
    for master in prs.slide_masters:
        _collect_footer_text(master, "slide master", doc)
        for layout in master.slide_layouts:
            _collect_footer_text(layout, f"layout '{layout.name}'", doc)

    # --- slides: body text, speaker notes, images ---
    for idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            _walk_shape(shape, f"slide {idx}", "content", doc)

        if slide.has_notes_slide:
            notes_tf = slide.notes_slide.notes_text_frame
            if notes_tf and notes_tf.text.strip():
                doc.text_units.append(
                    TextUnit(location=f"slide {idx} notes", kind="notes", text=notes_tf.text)
                )

    return doc


def _collect_footer_text(container, label: str, doc: ParsedDocument) -> None:
    for shape in getattr(container, "placeholders", []):
        try:
            ph_type = shape.placeholder_format.idx
        except Exception:
            ph_type = None
        if shape.has_text_frame and shape.text_frame.text.strip():
            if ph_type in FOOTER_PLACEHOLDER_IDX or "footer" in (shape.name or "").lower():
                doc.text_units.append(
                    TextUnit(location=label, kind="master_footer", text=shape.text_frame.text)
                )
    for shape in getattr(container, "shapes", []):
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            _extract_picture(shape, label, "layout" if "layout" in label else "master", doc)


def _walk_shape(shape, location: str, source: str, doc: ParsedDocument) -> None:
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for sub in shape.shapes:
            _walk_shape(sub, location, source, doc)
        return

    if shape.has_text_frame and shape.text_frame.text.strip():
        doc.text_units.append(TextUnit(location=location, kind="body", text=shape.text_frame.text))

    if shape.has_table:
        rows_text = []
        for row in shape.table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    rows_text.append(cell.text)
        if rows_text:
            doc.text_units.append(TextUnit(location=f"{location} table", kind="body", text="\n".join(rows_text)))

    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        _extract_picture(shape, location, source, doc)


def _extract_picture(shape, location: str, source: str, doc: ParsedDocument) -> None:
    try:
        image = shape.image
    except Exception:
        return
    data = image.blob
    doc.images.append(
        ExtractedImage(
            location=location,
            source="content" if source == "content" else source,  # "layout"/"master"
            data=data,
            ext=image.ext,
            occurrence_hash=hashlib.sha256(data).hexdigest(),
        )
    )
