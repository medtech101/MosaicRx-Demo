"""
Module 3 tests. PubMed/Bookshelf network calls are exercised for real (they
degrade gracefully to an empty list if this environment can't reach NCBI,
which is asserted separately with a mock so the parsing logic itself is
still covered without depending on outbound network access). Everything
else - static open-resource links, commercial link-only mode, and the
rating-based ranking - is fully exercised against a real temporary SQLite
database through the actual FastAPI app.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Concept
from app.services.resources import pubmed
from app.services.resources.commercial_links import build_commercial_links, DEFAULT_TEMPLATES


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
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


def _make_concept(session_factory, name="hypertension") -> int:
    db = session_factory()
    concept = Concept(canonical_name=name, aliases=[])
    db.add(concept)
    db.commit()
    db.refresh(concept)
    cid = concept.id
    db.close()
    return cid


def test_pubmed_esearch_esummary_parsing_with_mocked_transport():
    """Covers the real parsing contract (esearch idlist -> esummary docs)
    without depending on outbound network access to NCBI in this sandbox."""
    esearch_json = {"esearchresult": {"idlist": ["12345"]}}
    esummary_json = {"result": {"12345": {"title": "Hypertension: a review", "fulljournalname": "JAMA"}}}

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self._payload

    call_log = []

    def fake_get(self, url, params=None):
        call_log.append(url)
        if "esearch" in url:
            return FakeResponse(esearch_json)
        return FakeResponse(esummary_json)

    with patch("httpx.Client.get", new=fake_get):
        results = pubmed.search_pubmed_reviews("hypertension")

    assert len(results) == 1
    assert results[0].title == "Hypertension: a review"
    assert results[0].url == "https://pubmed.ncbi.nlm.nih.gov/12345/"
    assert any("esearch" in u for u in call_log)
    assert any("esummary" in u for u in call_log)


def test_pubmed_network_failure_degrades_to_empty_list():
    def raise_error(self, url, params=None):
        raise pubmed.httpx.ConnectError("blocked")

    with patch("httpx.Client.get", new=raise_error):
        assert pubmed.search_pubmed_reviews("hypertension") == []
        assert pubmed.search_bookshelf("hypertension") == []


def test_commercial_links_default_to_link_only(client):
    _, TestSession = client
    db = TestSession()
    links = build_commercial_links(db, "hypertension")
    db.close()

    assert {l["platform"] for l in links} == set(DEFAULT_TEMPLATES.keys())
    for link in links:
        assert link["mode"] == "link_only"
        assert "hypertension" in link["url"]


def test_get_resources_endpoint_includes_static_and_commercial_links(client):
    http_client, session_factory = client
    concept_id = _make_concept(session_factory)

    resp = http_client.get(f"/api/resources/concepts/{concept_id}")
    assert resp.status_code == 200
    sources = {r["source"] for r in resp.json()["resources"]}
    assert "openstax" in sources
    assert "medlineplus" in sources
    assert "amboss" in sources
    assert "boards_and_beyond" in sources
    assert "bootcamp" in sources


def test_ranked_resources_prioritizes_helpful_over_not_helpful(client):
    http_client, session_factory = client
    concept_id = _make_concept(session_factory)

    resources = http_client.get(f"/api/resources/concepts/{concept_id}").json()["resources"]
    openstax = next(r for r in resources if r["source"] == "openstax")
    medlineplus = next(r for r in resources if r["source"] == "medlineplus")

    http_client.post("/api/resources/ratings", json={
        "resource_id": medlineplus["id"], "concept_id": concept_id, "helpful": False,
    })
    http_client.post("/api/resources/ratings", json={
        "resource_id": openstax["id"], "concept_id": concept_id, "helpful": True,
    })

    ranked = http_client.get(f"/api/resources/concepts/{concept_id}/ranked").json()["resources"]
    ranked_ids_in_order = [r["id"] for r in ranked]
    assert ranked_ids_in_order.index(openstax["id"]) < ranked_ids_in_order.index(medlineplus["id"])
