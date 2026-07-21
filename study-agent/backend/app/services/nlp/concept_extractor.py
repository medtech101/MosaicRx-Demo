"""
Biomedical concept extraction.

Preferred path: scispaCy's en_core_sci_md pipeline (trained biomedical NER +
UMLS-style linking via scispacy's EntityLinker, when the UMLS knowledge base
is also installed). Pretrained scispaCy models are ~500MB-1GB and are
downloaded from an S3 bucket the first time - do this once wherever the app
is deployed (Replit has full internet access):

    pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_md-0.5.4.tar.gz

Fallback path (used automatically when that model isn't installed, e.g. in a
network-restricted sandbox): a curated seed vocabulary of high-yield med
school concepts matched with spaCy's PhraseMatcher, plus a heuristic that
also captures capitalized multi-word phrases ("Renin-Angiotensin System")
that look like named concepts but aren't in the seed list. This is a
deliberately coarser stand-in - it will miss many concepts a real biomedical
NER model would catch - and is logged loudly so it's never mistaken for the
real pipeline.
"""
import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger("nlp.concepts")

# A small high-yield seed vocabulary spanning systems commonly taught together
# early in med school - enough to demonstrate real cross-system bridging
# (e.g. renin-angiotensin system links renal/cardio/pharm) even without the
# full scispaCy + UMLS pipeline.
SEED_VOCABULARY = [
    # renal / cardio / pharm (deliberately cross-linked, per the spec's example)
    "renin-angiotensin system", "renin", "angiotensin ii", "aldosterone",
    "ace inhibitor", "ace inhibitors", "hypertension", "blood pressure",
    "glomerular filtration rate", "nephron", "juxtaglomerular apparatus",
    "sodium reabsorption", "potassium", "diuretic", "diuretics",
    "loop diuretic", "thiazide diuretic", "heart failure", "cardiac output",
    "left ventricular hypertrophy", "myocardial infarction", "atherosclerosis",
    "beta blocker", "beta blockers", "calcium channel blocker",
    "arb", "angiotensin receptor blocker",
    # renal
    "chronic kidney disease", "acute kidney injury", "creatinine",
    "proteinuria", "nephrotic syndrome", "nephritic syndrome",
    "renal tubular acidosis", "dialysis",
    # cardiovascular
    "arrhythmia", "atrial fibrillation", "ejection fraction",
    "coronary artery disease", "angina", "endocarditis", "pericarditis",
    "deep vein thrombosis", "pulmonary embolism",
    # pharmacology (general)
    "pharmacokinetics", "pharmacodynamics", "half life", "bioavailability",
    "first pass metabolism", "cytochrome p450", "drug clearance",
    "therapeutic index", "agonist", "antagonist", "receptor binding",
    # endocrine
    "diabetes mellitus", "insulin", "glucagon", "thyroid hormone",
    "hypothyroidism", "hyperthyroidism", "cortisol", "adrenal insufficiency",
    "cushing syndrome", "addison disease",
    # respiratory
    "asthma", "copd", "pneumonia", "pulmonary fibrosis", "pleural effusion",
    "hypoxia", "hypercapnia", "ventilation perfusion mismatch",
    # gi
    "peptic ulcer disease", "gastritis", "cirrhosis", "hepatitis",
    "pancreatitis", "inflammatory bowel disease", "crohn disease",
    "ulcerative colitis",
    # neuro
    "stroke", "seizure", "parkinson disease", "alzheimer disease",
    "multiple sclerosis", "neuropathy", "action potential",
    # heme/onc
    "anemia", "leukemia", "lymphoma", "thrombocytopenia", "coagulation cascade",
    "hemolysis",
    # micro/immuno
    "gram positive", "gram negative", "antibiotic resistance",
    "innate immunity", "adaptive immunity", "cytokine", "inflammation",
    "autoimmune disease",
]

CANONICAL_ALIASES = {
    "htn": "hypertension",
    "mi": "myocardial infarction",
    "ckd": "chronic kidney disease",
    "aki": "acute kidney injury",
    "gfr": "glomerular filtration rate",
    "dm": "diabetes mellitus",
    "afib": "atrial fibrillation",
    "a-fib": "atrial fibrillation",
    "ras": "renin-angiotensin system",
    "arbs": "angiotensin receptor blocker",
    "copd": "copd",
    "dvt": "deep vein thrombosis",
    "pe": "pulmonary embolism",
    "ace-i": "ace inhibitor",
    "acei": "ace inhibitor",
}

CAPITALIZED_PHRASE_RE = re.compile(
    r"\b([A-Z][a-z]+(?:[- ][A-Z][a-z]+){1,4})\b"
)


def canonicalize(text: str) -> str:
    key = text.strip().lower()
    key = re.sub(r"\s+", " ", key)
    key = CANONICAL_ALIASES.get(key, key)
    if key.endswith("s") and key[:-1] in SEED_VOCAB_SET:
        key = key[:-1]
    return key


SEED_VOCAB_SET = {v.lower() for v in SEED_VOCABULARY}


@dataclass
class ConceptSpan:
    text: str
    canonical: str
    start: int
    end: int


class ConceptExtractor:
    def __init__(self):
        self._nlp = None
        self._matcher = None
        self._mode = "unloaded"
        self._load()

    def _load(self):
        settings = get_settings()
        try:
            import spacy

            self._nlp = spacy.load(settings.scispacy_model)
            self._mode = "scispacy"
            logger.info("Loaded scispaCy model '%s' for concept extraction.", settings.scispacy_model)
            return
        except Exception as exc:
            logger.warning(
                "scispaCy model '%s' unavailable (%s). Falling back to a curated "
                "seed-vocabulary matcher for concept extraction - this WILL MISS "
                "most biomedical concepts a real model would catch. Install the "
                "model in an environment with internet access to activate full "
                "concept extraction: pip install <scispacy model wheel url>.",
                settings.scispacy_model, exc,
            )

        try:
            import spacy
            from spacy.matcher import PhraseMatcher

            self._nlp = spacy.blank("en")
            matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
            patterns = [self._nlp.make_doc(term) for term in SEED_VOCABULARY]
            matcher.add("SEED_CONCEPT", patterns)
            self._matcher = matcher
            self._mode = "fallback"
        except Exception as exc:
            logger.error("Could not initialize even the fallback concept matcher: %s", exc)
            self._mode = "unavailable"

    @property
    def mode(self) -> str:
        return self._mode

    def extract(self, text: str) -> list[ConceptSpan]:
        if not text.strip():
            return []

        if self._mode == "scispacy" and self._nlp is not None:
            doc = self._nlp(text)
            return [
                ConceptSpan(text=ent.text, canonical=canonicalize(ent.text), start=ent.start_char, end=ent.end_char)
                for ent in doc.ents
            ]

        if self._mode == "fallback" and self._nlp is not None and self._matcher is not None:
            doc = self._nlp(text)
            spans: list[ConceptSpan] = []
            seen_spans: set[tuple[int, int]] = set()
            for _, start, end in self._matcher(doc):
                span = doc[start:end]
                spans.append(ConceptSpan(text=span.text, canonical=canonicalize(span.text),
                                          start=span.start_char, end=span.end_char))
                seen_spans.add((span.start_char, span.end_char))
            for m in CAPITALIZED_PHRASE_RE.finditer(text):
                if any(s <= m.start() < e for s, e in seen_spans):
                    continue
                spans.append(ConceptSpan(text=m.group(1), canonical=canonicalize(m.group(1)),
                                          start=m.start(), end=m.end()))
            return spans

        return []


@lru_cache
def get_concept_extractor() -> ConceptExtractor:
    return ConceptExtractor()
