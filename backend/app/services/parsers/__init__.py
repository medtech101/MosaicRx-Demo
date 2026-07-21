from .base import ParsedDocument, TextUnit, ExtractedImage
from .pptx_parser import parse_pptx
from .docx_parser import parse_docx
from .pdf_parser import parse_pdf

_DISPATCH = {
    "pptx": parse_pptx,
    "docx": parse_docx,
    "pdf": parse_pdf,
}


def parse_document(path: str, doc_type: str) -> ParsedDocument:
    if doc_type not in _DISPATCH:
        raise ValueError(f"Unsupported document type: {doc_type}")
    return _DISPATCH[doc_type](path)


__all__ = ["parse_document", "ParsedDocument", "TextUnit", "ExtractedImage"]
