"""
Deterministic (no API call, nothing to scrape) search links into free
reference sites. These are plain URL templates against each site's public
search page, so they always "work" in the sense of loading a real search
results page for the concept - no scraping, no fabricated deep links to
specific articles.
"""
from urllib.parse import quote_plus


def openstax_ap_link(concept_name: str) -> str:
    return f"https://openstax.org/search?q={quote_plus(concept_name)}"


def medlineplus_link(concept_name: str) -> str:
    return f"https://medlineplus.gov/search/?query={quote_plus(concept_name)}"


def static_open_resources(concept_name: str) -> list[dict]:
    return [
        {"source": "openstax", "title": f"OpenStax A&P: {concept_name}", "url": openstax_ap_link(concept_name)},
        {"source": "medlineplus", "title": f"MedlinePlus: {concept_name}", "url": medlineplus_link(concept_name)},
    ]
