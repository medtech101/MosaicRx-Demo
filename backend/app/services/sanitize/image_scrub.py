"""
Image handling: EXIF stripping, repeated-logo/watermark detection, and OCR
scanning so text baked into images (letterhead, watermarked backgrounds)
doesn't silently bypass text-layer redaction.
"""
import io
import logging
from collections import Counter
from dataclasses import dataclass

from PIL import Image

from .blocklist import find_blocklist_matches
from ..parsers.base import ExtractedImage

logger = logging.getLogger("sanitize.image")

try:
    import pytesseract

    _OCR_AVAILABLE = True
except Exception:
    _OCR_AVAILABLE = False
    logger.warning("pytesseract/tesseract not available - image OCR blocklist scanning is disabled.")


@dataclass
class ImageDecision:
    image: ExtractedImage
    is_logo: bool
    ocr_text: str
    matched_terms: list[str]
    needs_review: bool


def strip_exif(data: bytes) -> bytes:
    try:
        img = Image.open(io.BytesIO(data))
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        buf = io.BytesIO()
        clean.save(buf, format=img.format or "PNG")
        return buf.getvalue()
    except Exception:
        return data


def ocr_text(data: bytes) -> str:
    if not _OCR_AVAILABLE:
        return ""
    try:
        img = Image.open(io.BytesIO(data))
        return pytesseract.image_to_string(img) or ""
    except Exception:
        return ""


def detect_repeated_hashes(images: list[ExtractedImage], min_occurrences: int = 2) -> set[str]:
    counts = Counter(img.occurrence_hash for img in images)
    return {h for h, c in counts.items() if c >= min_occurrences and h}


def evaluate_images(images: list[ExtractedImage], terms_by_category: dict[str, list[str]]) -> list[ImageDecision]:
    repeated_hashes = detect_repeated_hashes(images)
    decisions = []
    for img in images:
        is_layout_or_master = img.source in ("layout", "master", "header_footer")
        is_repeated = img.occurrence_hash in repeated_hashes
        is_logo = is_layout_or_master or is_repeated

        text = ocr_text(img.data)
        matches = find_blocklist_matches(text, terms_by_category) if text.strip() else []
        matched_terms = sorted({m.original for m in matches})

        decisions.append(
            ImageDecision(
                image=img,
                is_logo=is_logo,
                ocr_text=text,
                matched_terms=matched_terms,
                needs_review=bool(matched_terms) and not is_logo,
            )
        )
    return decisions
