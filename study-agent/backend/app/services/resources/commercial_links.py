"""
Commercial study platforms (Boards and Beyond, Bootcamp, AMBOSS) are
link-only by default - this app never scrapes them. It generates a deep
search link into each platform for a given concept from an editable URL
template (a `{query}` placeholder gets the concept name).

The seed templates below are a best-effort starting point - these
consumer ed-tech sites change their URL structure without notice and none
publish a stable public search API, so **verify/edit them once in
Settings** against your own logged-in session before trusting the links.

If AMBOSS_API_KEY / BNB_API_KEY / BOOTCAMP_API_KEY (Replit Secrets) are
set, the corresponding adapter below activates instead of the plain link -
today none of these platforms publish an official public API, so the
adapters are stubs that raise NotImplementedError until official API
access exists; the router catches that and falls back to link-only mode
automatically, so setting a key never breaks anything.
"""
from urllib.parse import quote_plus

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AppSettingKV

SETTINGS_KEY = "commercial_link_templates"

DEFAULT_TEMPLATES = {
    "amboss": "https://www.amboss.com/us/knowledge/search?q={query}",
    "boards_and_beyond": "https://www.boardsbeyond.com/search?query={query}",
    "bootcamp": "https://usmle-bootcamp.com/search?q={query}",
}

PLATFORM_LABELS = {
    "amboss": "AMBOSS",
    "boards_and_beyond": "Boards and Beyond",
    "bootcamp": "Bootcamp",
}


def get_templates(db: Session) -> dict[str, str]:
    row = db.get(AppSettingKV, SETTINGS_KEY)
    if row and isinstance(row.value, dict):
        return {**DEFAULT_TEMPLATES, **row.value}
    return dict(DEFAULT_TEMPLATES)


def set_template(db: Session, platform: str, url_template: str) -> dict[str, str]:
    row = db.get(AppSettingKV, SETTINGS_KEY)
    current = dict(row.value) if row and isinstance(row.value, dict) else dict(DEFAULT_TEMPLATES)
    current[platform] = url_template
    if row:
        row.value = current
    else:
        db.add(AppSettingKV(key=SETTINGS_KEY, value=current))
    db.commit()
    return current


class CommercialApiAdapter:
    """Stub base class. A real adapter would call the platform's official
    API to fetch a specific article/lesson id for the concept; none of
    these platforms currently publish one, so every adapter below simply
    signals "not implemented" and the caller falls back to the link."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, concept_name: str) -> dict | None:
        raise NotImplementedError("No official public API is configured for this platform yet.")


class AmbossAdapter(CommercialApiAdapter):
    pass


class BoardsAndBeyondAdapter(CommercialApiAdapter):
    pass


class BootcampAdapter(CommercialApiAdapter):
    pass


_ADAPTERS = {
    "amboss": (AmbossAdapter, "amboss_api_key"),
    "boards_and_beyond": (BoardsAndBeyondAdapter, "bnb_api_key"),
    "bootcamp": (BootcampAdapter, "bootcamp_api_key"),
}


def build_commercial_links(db: Session, concept_name: str) -> list[dict]:
    settings = get_settings()
    templates = get_templates(db)
    query = quote_plus(concept_name)

    results = []
    for platform, url_template in templates.items():
        adapter_cls, key_attr = _ADAPTERS.get(platform, (None, None))
        api_key = getattr(settings, key_attr, "") if key_attr else ""

        api_result = None
        if api_key and adapter_cls:
            try:
                api_result = adapter_cls(api_key).fetch(concept_name)
            except NotImplementedError:
                api_result = None

        if api_result:
            results.append({"platform": platform, "label": PLATFORM_LABELS.get(platform, platform), **api_result})
        else:
            results.append({
                "platform": platform,
                "label": PLATFORM_LABELS.get(platform, platform),
                "url": url_template.format(query=query),
                "mode": "link_only",
            })
    return results
