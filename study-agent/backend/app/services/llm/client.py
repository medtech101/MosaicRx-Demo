"""
The only path through which this app calls an external LLM (summarization,
flashcard generation). Two things are enforced here, in code, not just by
convention:

1. The API key comes from an environment variable only (Replit Secrets
   inject it as one) - it is never hardcoded, never logged, never returned
   in any response.
2. Every call re-scans its own source text against the live blocklist
   before sending anything over the network. Callers are expected to pass
   already-sanitized text, but this is the enforcement point: if a
   blocklist term somehow survives into what's about to be sent, the call
   is refused outright rather than trusting the caller got it right.

If no key is configured (e.g. this sandbox, or a fresh install before the
user has added one), calls return None and callers fall back to a
deterministic, non-LLM generation path - the export center must work
without an LLM configured at all.
"""
import logging

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.sanitize.blocklist import find_blocklist_matches
from app.routers.settings import terms_by_category

logger = logging.getLogger("llm.client")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
TIMEOUT = 30.0


class UnsanitizedContentError(Exception):
    """Raised when source text about to be sent to the LLM still matches
    the blocklist - the call is refused, never sent."""


def _assert_sanitized(db: Session, *texts: str) -> None:
    terms = terms_by_category(db)
    for text in texts:
        matches = find_blocklist_matches(text, terms)
        if matches:
            raise UnsanitizedContentError(
                f"Refusing LLM call: source text still contains a blocklisted term "
                f"('{matches[0].original}'). This should never happen for content that "
                f"went through the sanitization pipeline - not sending anything."
            )


def call_llm(db: Session, system: str, user_prompt: str, sanitized_sources: list[str], max_tokens: int = 1024) -> str | None:
    """Returns the model's text response, or None if no API key is
    configured (callers must have a deterministic fallback)."""
    settings = get_settings()
    if not settings.llm_api_key:
        logger.info("No LLM_API_KEY configured - skipping LLM call, caller should use its fallback.")
        return None

    _assert_sanitized(db, user_prompt, *sanitized_sources)

    if settings.llm_provider != "anthropic":
        logger.warning("Unsupported LLM_PROVIDER '%s' - skipping LLM call.", settings.llm_provider)
        return None

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": settings.llm_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return "".join(block.get("text", "") for block in data.get("content", []))
    except httpx.HTTPError as exc:
        logger.warning("LLM call failed (%s) - caller should use its fallback.", exc)
        return None
