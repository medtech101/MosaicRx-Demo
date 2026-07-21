import datetime as dt
import zipfile
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Concept, ConceptEdge, Document, BlocklistTerm, ScheduleBlock, Week
from app.services.llm.client import call_llm, UnsanitizedContentError
from app.services.export.flashcards import generate_flashcards, flashcards_to_anki_csv
from app.services.export.graph_export import export_graphml, export_graph_json, export_graph_png
from app.services.export.reports import bridge_concepts_report, cluster_summary_report
from app.services.export.bundle import build_export_bundle


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test_api.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c, TestSession
    app.dependency_overrides.clear()


def _seed_two_linked_concepts(db):
    a = Concept(canonical_name="hypertension")
    b = Concept(canonical_name="ace inhibitor")
    db.add_all([a, b])
    db.commit()
    db.add(ConceptEdge(concept_a_id=min(a.id, b.id), concept_b_id=max(a.id, b.id), scope="slide", weight=2.0))
    db.commit()
    return a, b


def test_llm_client_returns_none_without_api_key(db_session):
    assert call_llm(db_session, "system", "hello", []) is None


def test_llm_client_refuses_unsanitized_source_text(db_session, monkeypatch):
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_API_KEY", "fake-key-for-test")
    get_settings.cache_clear()
    try:
        db_session.add(BlocklistTerm(term="Springfield Medical School", category="institution"))
        db_session.commit()

        with pytest.raises(UnsanitizedContentError):
            call_llm(db_session, "system", "Notes from Springfield Medical School", [])
    finally:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        get_settings.cache_clear()


def test_llm_client_calls_api_when_key_present_and_content_clean(db_session, monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("LLM_API_KEY", "fake-key-for-test")
    get_settings.cache_clear()

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"text": "Front: What is X?\nBack: X is Y."}]}

    def fake_post(self, url, headers=None, json=None):
        assert "api.anthropic.com" in url
        return FakeResponse()

    try:
        with patch("httpx.Client.post", new=fake_post):
            result = call_llm(db_session, "system", "clean prompt", ["clean prompt"])
        assert "Front: What is X?" in result
    finally:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        get_settings.cache_clear()


def test_flashcards_fallback_generates_cards_without_llm(db_session):
    _seed_two_linked_concepts(db_session)
    cards = generate_flashcards(db_session)
    assert len(cards) == 2
    assert all(c["front"] and c["back"] for c in cards)
    csv_text = flashcards_to_anki_csv(cards)
    assert "hypertension" in csv_text.lower() or "ace inhibitor" in csv_text.lower()


def test_graph_exports_produce_valid_output(db_session):
    _seed_two_linked_concepts(db_session)

    graphml = export_graphml(db_session)
    assert "<graphml" in graphml

    payload = export_graph_json(db_session)
    assert len(payload["nodes"]) == 2
    assert len(payload["edges"]) == 1

    png_bytes = export_graph_png(db_session)
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes


def test_reports_render_markdown(db_session):
    _seed_two_linked_concepts(db_session)
    bridge_md = bridge_concepts_report(db_session)
    cluster_md = cluster_summary_report(db_session)
    assert bridge_md.startswith("# Bridge Concepts")
    assert cluster_md.startswith("# Cluster Summary")


def test_bundle_builds_a_valid_zip_with_expected_entries(db_session):
    _seed_two_linked_concepts(db_session)
    zip_bytes = build_export_bundle(db_session)
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        names = set(zf.namelist())
    assert "reports/bridge_concepts.md" in names
    assert "reports/cluster_summary.md" in names
    assert "flashcards/flashcards.csv" in names
    assert "schedule/schedule.csv" in names
    assert "schedule/schedule.ics" in names
    assert "resources/resource_ratings.csv" in names
    assert "graph/graph.json" in names
    assert "graph/graph.graphml" in names
    assert "graph/graph.png" in names


def test_bundle_refuses_when_a_leak_survived_sanitization(db_session):
    """Simulates a defect elsewhere in the pipeline that let a blocklisted
    term slip into a confirmed document's sanitized markdown - the export
    center's own final scan must still catch it and refuse to export."""
    db_session.add(BlocklistTerm(term="Springfield Medical School", category="institution"))
    doc = Document(
        original_filename="leaky.pptx", doc_type="pptx", status="confirmed",
        sanitized_markdown="Notes that mention Springfield Medical School by mistake.",
        confirmed_at=dt.datetime.utcnow(),
    )
    db_session.add(doc)
    db_session.commit()

    with pytest.raises(ValueError, match="blocklist"):
        build_export_bundle(db_session)


def test_export_endpoints_download_through_the_real_app(client):
    http_client, session_factory = client
    db = session_factory()
    _seed_two_linked_concepts(db)
    db.close()

    resp = http_client.get("/api/export/flashcards.csv")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]

    resp = http_client.get("/api/export/graph/json")
    assert resp.status_code == 200
    assert len(resp.json()["nodes"]) == 2

    resp = http_client.get("/api/export/graph/png")
    assert resp.status_code == 200
    assert resp.content[:4] == b"\x89PNG"

    resp = http_client.get("/api/export/bundle.zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"


def test_bundle_endpoint_returns_422_on_leak(client):
    http_client, session_factory = client
    db = session_factory()
    db.add(BlocklistTerm(term="Springfield Medical School", category="institution"))
    db.add(Document(
        original_filename="leaky.pptx", doc_type="pptx", status="confirmed",
        sanitized_markdown="Mentions Springfield Medical School.",
        confirmed_at=dt.datetime.utcnow(),
    ))
    db.commit()
    db.close()

    resp = http_client.get("/api/export/bundle.zip")
    assert resp.status_code == 422
