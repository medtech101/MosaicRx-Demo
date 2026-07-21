"""
NER-based redaction for person/organization names the blocklist misses.

Requires the spaCy model configured via SPACY_NER_MODEL (default
en_core_web_sm). Pretrained spaCy models are downloaded from GitHub release
assets on first setup (`python -m spacy download en_core_web_sm`) - do this
once wherever the app is deployed (e.g. Replit, which has full internet
access). If the model isn't installed, this module falls back to a coarse
heuristic (title-cased word sequences following honorifics like "Dr."/"Professor")
and logs a loud warning: that fallback is NOT a substitute for real NER and
should never be relied on for real de-identification.
"""
import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger("sanitize.ner")

HONORIFIC_FALLBACK_RE = re.compile(
    r"\b(?:Dr|Prof|Professor|Mr|Mrs|Ms)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}"
)


@dataclass
class NerMatch:
    start: int
    end: int
    text: str
    label: str  # "PERSON" / "ORG"


class NerRedactor:
    def __init__(self):
        self._nlp = None
        self._mode = "unloaded"
        self._load()

    def _load(self):
        settings = get_settings()
        try:
            import spacy

            self._nlp = spacy.load(settings.spacy_ner_model)
            self._mode = "model"
            logger.info("Loaded spaCy NER model '%s' for name/org redaction.", settings.spacy_ner_model)
        except Exception as exc:  # OSError if model missing, ImportError if spacy missing
            self._nlp = None
            self._mode = "fallback"
            logger.warning(
                "spaCy model '%s' unavailable (%s). Falling back to a coarse honorific-based "
                "heuristic for person-name redaction. This fallback WILL MISS many names — "
                "run `python -m spacy download %s` in an environment with internet access "
                "before relying on this for real de-identification.",
                settings.spacy_ner_model, exc, settings.spacy_ner_model,
            )

    @property
    def mode(self) -> str:
        return self._mode

    def find_entities(self, text: str) -> list[NerMatch]:
        if self._mode == "model" and self._nlp is not None:
            doc = self._nlp(text)
            return [
                NerMatch(ent.start_char, ent.end_char, ent.text, ent.label_)
                for ent in doc.ents
                if ent.label_ in ("PERSON", "ORG")
            ]
        return [
            NerMatch(m.start(), m.end(), m.group(0), "PERSON")
            for m in HONORIFIC_FALLBACK_RE.finditer(text)
        ]


@lru_cache
def get_ner_redactor() -> NerRedactor:
    return NerRedactor()
