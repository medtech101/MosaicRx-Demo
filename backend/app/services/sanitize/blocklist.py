"""
Deterministic redaction: user-supplied blocklist terms, plus unconditional
patterns (email addresses, and URLs that match a blocklist term/domain).
This runs regardless of whether the spaCy NER model is available, so it is
the guaranteed floor of the sanitization pipeline.
"""
import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"\bhttps?://[^\s)>\]]+", re.IGNORECASE)


@dataclass
class Match:
    start: int
    end: int
    original: str
    category: str
    replacement: str


def _build_term_pattern(terms: list[str]) -> re.Pattern | None:
    escaped = [re.escape(t) for t in terms if t.strip()]
    if not escaped:
        return None
    # longest-first so "School of Medicine" wins over "Medicine"
    escaped.sort(key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


def find_blocklist_matches(text: str, terms_by_category: dict[str, list[str]]) -> list[Match]:
    matches: list[Match] = []

    all_terms: list[tuple[str, str]] = []
    for category, terms in terms_by_category.items():
        for t in terms:
            all_terms.append((t, category))

    pattern = _build_term_pattern([t for t, _ in all_terms])
    term_to_category = {t.lower(): c for t, c in all_terms}
    if pattern:
        for m in pattern.finditer(text):
            category = term_to_category.get(m.group(0).lower(), "custom")
            matches.append(
                Match(m.start(), m.end(), m.group(0), category, f"[REDACTED:{category.upper()}]")
            )

    for m in EMAIL_RE.finditer(text):
        matches.append(Match(m.start(), m.end(), m.group(0), "email", "[REDACTED:EMAIL]"))

    domain_terms = [t for c, ts in terms_by_category.items() for t in ts]
    for m in URL_RE.finditer(text):
        url = m.group(0)
        if any(t.lower() in url.lower() for t in domain_terms):
            matches.append(Match(m.start(), m.end(), url, "url", "[REDACTED:INTERNAL_URL]"))

    return matches
