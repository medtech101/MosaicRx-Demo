"""
Shared data model produced by every format-specific parser (pptx/docx/pdf).
Sanitization operates uniformly over this structure so the redaction engine
does not need to know about file formats.
"""
from dataclasses import dataclass, field
from typing import Literal

UnitKind = Literal["body", "notes", "header", "footer", "master_footer"]
ImageSource = Literal["content", "layout", "master", "header_footer"]


@dataclass
class TextUnit:
    location: str          # human-readable location, e.g. "slide 3", "paragraph 12"
    kind: UnitKind
    text: str


@dataclass
class ExtractedImage:
    location: str
    source: ImageSource
    data: bytes
    ext: str                # "png", "jpeg", ...
    occurrence_hash: str = ""  # content hash, used for repeated-logo detection


@dataclass
class ParsedDocument:
    doc_type: str
    unit_count: int                     # slide/page count
    text_units: list[TextUnit] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)
    core_properties: dict[str, str] = field(default_factory=dict)
