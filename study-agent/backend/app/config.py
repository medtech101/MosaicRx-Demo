"""
Central configuration. All secrets are read from environment variables only -
never hardcoded. On Replit, set these under the Secrets tool (they are injected
as env vars automatically). Locally, copy .env.example to .env.
"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"          # transient, originals deleted after sanitization confirm
SANITIZED_DIR = DATA_DIR / "sanitized"      # only sanitized content lives here long-term
EXPORTS_DIR = DATA_DIR / "exports"
MODELS_DIR = DATA_DIR / "models"

for d in (DATA_DIR, UPLOADS_DIR, SANITIZED_DIR, EXPORTS_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- storage ---
    database_url: str = f"sqlite:///{(DATA_DIR / 'study_agent.db').as_posix()}"

    # --- LLM (summarization, flashcard generation) ---
    llm_api_key: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-5"

    # --- spaCy / scispaCy NLP models ---
    spacy_ner_model: str = "en_core_web_sm"
    scispacy_model: str = "en_core_sci_md"

    # --- optional commercial platform API keys (link-only mode if absent) ---
    amboss_api_key: str = ""
    bnb_api_key: str = ""
    bootcamp_api_key: str = ""

    # --- NCBI E-utilities (optional, raises rate limits if set) ---
    ncbi_api_key: str = ""
    ncbi_email: str = ""

    # --- app ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    app_secret: str = "change-me-dev-only"


@lru_cache
def get_settings() -> Settings:
    return Settings()
