"""Request body schemas.

OCR and Speech currently take multipart file uploads (``UploadFile``), which
FastAPI validates without a Pydantic model — so there is nothing to define
here yet. This module exists for the first future endpoint that needs a JSON
request body (e.g. translation target language, per PRD §97) so it has an
obvious home without inventing a new file.
"""
