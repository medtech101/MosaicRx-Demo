import datetime as dt
from pydantic import BaseModel


class BlocklistTermOut(BaseModel):
    id: int
    term: str
    category: str
    model_config = {"from_attributes": True}


class BlocklistTermIn(BaseModel):
    term: str
    category: str = "custom"


class RedactionEntryOut(BaseModel):
    id: int
    location: str
    category: str
    original_text: str
    replacement_text: str
    status: str
    model_config = {"from_attributes": True}


class ImageFlagOut(BaseModel):
    id: int
    location: str
    reason: str
    ocr_text: str | None = None
    matched_terms: list[str] | None = None
    action: str
    thumbnail_path: str | None = None
    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    original_filename: str
    doc_type: str
    status: str
    unit_count: int
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class DocumentReviewOut(BaseModel):
    document: DocumentOut
    redactions: list[RedactionEntryOut]
    image_flags: list[ImageFlagOut]
    sanitized_markdown_preview: str


class RedactionDecision(BaseModel):
    id: int
    approve: bool  # True = keep redacted (default); False = restore original text (user override)


class ImageDecisionIn(BaseModel):
    id: int
    action: str  # "removed" | "kept"


class ConfirmRequest(BaseModel):
    redaction_decisions: list[RedactionDecision] = []
    image_decisions: list[ImageDecisionIn] = []
