# Mistral AI Workspace — Backend

FastAPI service that is the only thing allowed to talk to Mistral (OCR +
Voxtral Speech-to-Text). See [`../docs/prd/05-api-spec.md`](../docs/prd/05-api-spec.md)
for the full endpoint contract and [`../docs/adr/0001-service-layer-and-transport-boundary.md`](../docs/adr/0001-service-layer-and-transport-boundary.md)
for why it's structured this way.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Fill in `MISTRAL_API_KEY` in `.env` — without it, `/api/v1/ocr` and
`/api/v1/speech/*` return `503 Service Unavailable` (the health endpoint
still works so you can verify the server itself is up).

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/api/v1/health`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Structure

```
app/
  api/         routers — thin, no business logic (health, ocr, speech)
  services/    the only modules that import the Mistral SDK
  schemas/     Pydantic request/response models (API boundary)
  middleware/  CORS, request-ID + timing
  core/        settings, constants, exceptions, shared Mistral client
```

## Tests

```bash
pytest
```
