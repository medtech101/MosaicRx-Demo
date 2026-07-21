# Personal Study Agent - single-image build.
# One container serves both the UI and the API on one port, so it deploys to
# any container host (Render, Railway, Fly.io, a plain VPS, etc.).

# --- stage 1: build the React frontend --------------------------------------
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- stage 2: python runtime serving UI + API -------------------------------
FROM python:3.11-slim AS runtime

# tesseract powers the OCR blocklist scan on images during sanitization.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Best-effort NLP models for stronger de-identification / concept extraction.
# If the build network blocks these, the app still runs on its fallbacks.
RUN python -m spacy download en_core_web_sm || true
RUN pip install --no-cache-dir \
    "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_md-0.5.4.tar.gz" \
    || true

COPY backend/ /app/backend/
# The built SPA - main.py serves it from ../frontend/dist relative to backend.
COPY --from=frontend /frontend/dist /app/frontend/dist

ENV PORT=8000
EXPOSE 8000
# Secrets (LLM_API_KEY, NCBI_*, etc.) are supplied at run time via -e / the
# host's secret manager - never baked into the image.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
