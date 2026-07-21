"""
Free, open NCBI E-utilities client: PubMed review articles and NCBI
Bookshelf chapters (StatPearls especially). Public API, no key required,
though an email + NCBI_API_KEY (Replit Secret) raise the anonymous rate
limit from 3 req/sec to 10 req/sec - see
https://www.ncbi.nlm.nih.gov/books/NBK25497/ for the documented contract
this client follows (esearch -> esummary).

Network failures (including this app being run somewhere without outbound
internet) degrade gracefully to an empty result rather than raising, since
resource enrichment is a nice-to-have layered on top of the user's own
sanitized notes, never a hard dependency.
"""
import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger("resources.pubmed")

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT = 8.0


@dataclass
class OpenResource:
    title: str
    url: str
    source: str  # "pubmed" | "bookshelf"
    summary: str | None = None


def _common_params() -> dict:
    settings = get_settings()
    params = {"tool": "personal-study-agent", "retmode": "json"}
    if settings.ncbi_email:
        params["email"] = settings.ncbi_email
    if settings.ncbi_api_key:
        params["api_key"] = settings.ncbi_api_key
    return params


def _esearch(db: str, term: str, retmax: int) -> list[str]:
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(
            f"{EUTILS_BASE}/esearch.fcgi",
            params={**_common_params(), "db": db, "term": term, "retmax": retmax, "sort": "relevance"},
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])


def _esummary(db: str, ids: list[str]) -> dict:
    if not ids:
        return {}
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(
            f"{EUTILS_BASE}/esummary.fcgi",
            params={**_common_params(), "db": db, "id": ",".join(ids)},
        )
        resp.raise_for_status()
        return resp.json().get("result", {})


def search_pubmed_reviews(concept_name: str, max_results: int = 5) -> list[OpenResource]:
    """Review articles only (publication type filter), since those are the
    most useful high-yield summaries for a med student, not primary research."""
    term = f"{concept_name}[Title/Abstract] AND review[pt]"
    try:
        ids = _esearch("pubmed", term, max_results)
        summaries = _esummary("pubmed", ids)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("PubMed lookup failed for '%s': %s", concept_name, exc)
        return []

    out = []
    for uid in ids:
        doc = summaries.get(uid)
        if not doc:
            continue
        out.append(OpenResource(
            title=doc.get("title", concept_name),
            url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            source="pubmed",
            summary=doc.get("fulljournalname"),
        ))
    return out


def search_bookshelf(concept_name: str, max_results: int = 3, statpearls_only: bool = True) -> list[OpenResource]:
    """NCBI Bookshelf chapters, filtered to StatPearls by default since those
    are the concise clinical-reference chapters students actually use."""
    term = f"{concept_name} AND statpearls[book]" if statpearls_only else concept_name
    try:
        ids = _esearch("books", term, max_results)
        summaries = _esummary("books", ids)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Bookshelf lookup failed for '%s': %s", concept_name, exc)
        return []

    out = []
    for uid in ids:
        doc = summaries.get(uid)
        if not doc:
            continue
        book_id = doc.get("accession") or uid
        out.append(OpenResource(
            title=doc.get("title", concept_name),
            url=f"https://www.ncbi.nlm.nih.gov/books/{book_id}/",
            source="bookshelf",
            summary=doc.get("booktitle"),
        ))
    return out
