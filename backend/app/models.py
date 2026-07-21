import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


def now() -> dt.datetime:
    return dt.datetime.utcnow()


# ---------------------------------------------------------------------------
# Module 1: Ingestion & de-identification
# ---------------------------------------------------------------------------

class BlocklistTerm(Base):
    __tablename__ = "blocklist_terms"
    id = Column(Integer, primary_key=True)
    term = Column(String, nullable=False, unique=True)
    category = Column(String, default="custom")  # institution/campus/course_code/person/email/url/custom
    created_at = Column(DateTime, default=now)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    original_filename = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # pptx/pdf/docx
    status = Column(String, default="pending_review")  # processing/pending_review/confirmed/rejected/error
    upload_path = Column(String, nullable=True)     # deleted once confirmed
    sanitized_path = Column(String, nullable=True)   # only populated after confirmation
    sanitized_markdown = Column(Text, nullable=True)
    unit_count = Column(Integer, default=0)  # slide/page count
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=True)
    created_at = Column(DateTime, default=now)
    confirmed_at = Column(DateTime, nullable=True)

    redactions = relationship("RedactionEntry", back_populates="document", cascade="all, delete-orphan")
    image_flags = relationship("ImageFlag", back_populates="document", cascade="all, delete-orphan")
    units = relationship("DocumentUnit", back_populates="document", cascade="all, delete-orphan")
    week = relationship("Week", back_populates="documents")


class DocumentUnit(Base):
    """Original text per parsed unit, kept only until the document is
    confirmed or rejected - needed to let the user selectively restore a
    false-positive redaction before the final sanitized note is written.
    Deleted along with the rest of the staging data on confirm/reject."""
    __tablename__ = "document_units"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    location = Column(String)
    kind = Column(String)
    original_text = Column(Text)
    order_index = Column(Integer, default=0)

    document = relationship("Document", back_populates="units")


class RedactionEntry(Base):
    __tablename__ = "redaction_entries"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    location = Column(String)  # e.g. "slide 4", "paragraph 12", "page 3", "metadata:author"
    kind = Column(String, nullable=True)  # body/notes/header/footer/metadata (matches DocumentUnit.kind)
    category = Column(String)  # blocklist/ner_person/ner_org/email/url/metadata/logo_image/ocr_image
    original_text = Column(Text)
    replacement_text = Column(Text)
    status = Column(String, default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, default=now)

    document = relationship("Document", back_populates="redactions")


class ImageFlag(Base):
    __tablename__ = "image_flags"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    location = Column(String)
    reason = Column(String)  # logo_heuristic / ocr_blocklist_match
    ocr_text = Column(Text, nullable=True)
    matched_terms = Column(JSON, nullable=True)
    action = Column(String, default="pending")  # pending/removed/kept
    thumbnail_path = Column(String, nullable=True)
    ext = Column(String, nullable=True)

    document = relationship("Document", back_populates="image_flags")


# ---------------------------------------------------------------------------
# Module 2: Knowledge graph
# ---------------------------------------------------------------------------

class Concept(Base):
    __tablename__ = "concepts"
    id = Column(Integer, primary_key=True)
    canonical_name = Column(String, nullable=False, unique=True)
    aliases = Column(JSON, default=list)
    umls_cui = Column(String, nullable=True)
    semantic_type = Column(String, nullable=True)
    first_seen_at = Column(DateTime, default=now)


class ConceptOccurrence(Base):
    __tablename__ = "concept_occurrences"
    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    location = Column(String)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=True)


class ConceptEdge(Base):
    __tablename__ = "concept_edges"
    id = Column(Integer, primary_key=True)
    concept_a_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    concept_b_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    weight = Column(Float, default=1.0)
    scope = Column(String, default="slide")  # slide/lecture
    __table_args__ = (UniqueConstraint("concept_a_id", "concept_b_id", "scope", name="uq_edge"),)


class GraphSnapshot(Base):
    """A cached computed layer (centrality/community) for the cumulative graph."""
    __tablename__ = "graph_snapshots"
    id = Column(Integer, primary_key=True)
    computed_at = Column(DateTime, default=now)
    bridge_concepts = Column(JSON, default=list)   # ranked [{concept_id, betweenness}]
    communities = Column(JSON, default=dict)        # {concept_id: community_id}
    community_labels = Column(JSON, default=dict)   # {community_id: label}
    new_week_id = Column(Integer, ForeignKey("weeks.id"), nullable=True)


# ---------------------------------------------------------------------------
# Module 3: Resource enrichment
# ---------------------------------------------------------------------------

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    source = Column(String, nullable=False)  # pubmed/bookshelf/openstax/medlineplus/amboss/bootcamp/bnb
    title = Column(String)
    url = Column(String)
    summary = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=now)
    __table_args__ = (UniqueConstraint("concept_id", "source", "url", name="uq_resource"),)


class ResourceRating(Base):
    __tablename__ = "resource_ratings"
    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    helpful = Column(Boolean, nullable=False)
    used_at = Column(DateTime, default=now)
    note = Column(String, nullable=True)


# ---------------------------------------------------------------------------
# Module 4: Scheduler
# ---------------------------------------------------------------------------

class Week(Base):
    __tablename__ = "weeks"
    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=now)

    documents = relationship("Document", back_populates="week")


class ConceptReviewState(Base):
    """SM-2 style spaced-repetition state, one row per concept cluster."""
    __tablename__ = "concept_review_states"
    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, unique=True)
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Float, default=1.0)
    repetitions = Column(Integer, default=0)
    due_date = Column(DateTime, default=now)
    last_confidence = Column(Integer, nullable=True)  # 1-4
    last_reviewed_at = Column(DateTime, nullable=True)


class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"
    id = Column(Integer, primary_key=True)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)
    day = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    block_type = Column(String, default="new")  # new/review/taper
    status = Column(String, default="planned")  # planned/completed/skipped
    confidence_rating = Column(Integer, nullable=True)
    label = Column(String, nullable=True)


class AppSettingKV(Base):
    __tablename__ = "app_settings"
    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=now)
