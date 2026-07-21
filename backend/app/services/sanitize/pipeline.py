"""
Orchestrates the mandatory sanitization pass required before any uploaded
content is stored or processed further:
  1. text redaction (blocklist + spaCy NER)
  2. metadata scrubbing
  3. image handling (logo removal + OCR blocklist flag for manual review)
  4. produces a diff-style review payload; nothing is persisted as "confirmed"
     until the user approves it via the review queue.
"""
from dataclasses import dataclass, field

from app.services.parsers import parse_document, ParsedDocument, TextUnit
from .blocklist import find_blocklist_matches, Match
from .ner_redact import get_ner_redactor
from .image_scrub import evaluate_images, strip_exif, ImageDecision

NER_LABEL_CATEGORY = {"PERSON": "ner_person", "ORG": "ner_org"}


@dataclass
class TextRedaction:
    location: str
    kind: str
    category: str
    original: str
    replacement: str
    span: tuple[int, int]


@dataclass
class SanitizedUnit:
    location: str
    kind: str
    original_text: str
    sanitized_text: str
    redactions: list[TextRedaction] = field(default_factory=list)


@dataclass
class SanitizationResult:
    doc_type: str
    unit_count: int
    units: list[SanitizedUnit]
    metadata_redactions: list[TextRedaction]
    image_decisions: list[ImageDecision]
    sanitized_markdown: str


def _merge_spans(blocklist_matches: list[Match], ner_matches) -> list[Match]:
    all_matches = list(blocklist_matches)
    for ent in ner_matches:
        category = NER_LABEL_CATEGORY.get(ent.label, "ner_other")
        all_matches.append(Match(ent.start, ent.end, ent.text, category, f"[REDACTED:{category.upper()}]"))

    all_matches.sort(key=lambda m: (m.start, -(m.end - m.start)))
    merged: list[Match] = []
    last_end = -1
    for m in all_matches:
        if m.start >= last_end:
            merged.append(m)
            last_end = m.end
        # else: overlaps a higher-priority (earlier/longer) match already kept - drop it
    return merged


def _apply_matches(text: str, matches: list[Match]) -> tuple[str, list[TextRedaction]]:
    if not matches:
        return text, []
    out = []
    redactions = []
    cursor = 0
    for m in matches:
        out.append(text[cursor:m.start])
        out.append(m.replacement)
        redactions.append(
            TextRedaction(
                location="", kind="", category=m.category,
                original=m.original, replacement=m.replacement, span=(m.start, m.end),
            )
        )
        cursor = m.end
    out.append(text[cursor:])
    return "".join(out), redactions


def sanitize_text_unit(unit: TextUnit, terms_by_category: dict[str, list[str]]) -> SanitizedUnit:
    blocklist_matches = find_blocklist_matches(unit.text, terms_by_category)
    ner_matches = get_ner_redactor().find_entities(unit.text)
    merged = _merge_spans(blocklist_matches, ner_matches)
    sanitized, redactions = _apply_matches(unit.text, merged)
    for r in redactions:
        r.location = unit.location
        r.kind = unit.kind
    return SanitizedUnit(
        location=unit.location, kind=unit.kind,
        original_text=unit.text, sanitized_text=sanitized, redactions=redactions,
    )


def sanitize_metadata(parsed: ParsedDocument) -> list[TextRedaction]:
    redactions = []
    for field_name, value in parsed.core_properties.items():
        if not value:
            continue
        redactions.append(
            TextRedaction(
                location=f"metadata:{field_name}", kind="metadata", category="metadata",
                original=value, replacement="", span=(0, len(value)),
            )
        )
    return redactions


def build_markdown(units: list[SanitizedUnit]) -> str:
    lines = []
    current_location = None
    for u in units:
        if u.kind in ("footer", "master_footer", "header"):
            continue  # institutional chrome - never part of study content
        if u.location != current_location:
            lines.append(f"\n### {u.location}\n")
            current_location = u.location
        if u.kind == "notes":
            lines.append(f"> **Speaker notes:** {u.sanitized_text}\n")
        else:
            lines.append(u.sanitized_text + "\n")
    return "\n".join(lines).strip()


def run_ingestion_pipeline(path: str, doc_type: str, terms_by_category: dict[str, list[str]]) -> SanitizationResult:
    parsed = parse_document(path, doc_type)

    units = [sanitize_text_unit(u, terms_by_category) for u in parsed.text_units]
    metadata_redactions = sanitize_metadata(parsed)
    image_decisions = evaluate_images(parsed.images, terms_by_category)
    markdown = build_markdown(units)

    return SanitizationResult(
        doc_type=parsed.doc_type,
        unit_count=parsed.unit_count,
        units=units,
        metadata_redactions=metadata_redactions,
        image_decisions=image_decisions,
        sanitized_markdown=markdown,
    )
