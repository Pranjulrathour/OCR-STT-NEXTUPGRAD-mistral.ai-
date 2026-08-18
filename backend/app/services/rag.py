"""Persistent RAG index backed by FAISS and Mistral embeddings.

The OCR pipeline remains the source of truth for document text.  This service
only chunks OCR pages, embeds the chunks, stores vectors, and retrieves the
most relevant chunks for chat.  Metadata is kept alongside the FAISS index so
responses can cite filename and page number.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

import faiss
import httpx
import numpy as np

from app.core.config import Settings
from app.schemas.response import OcrSuccessResponse

logger = logging.getLogger(__name__)

_INDEX_DIR = Path(os.getenv("RAG_INDEX_DIR", "data/rag"))
_INDEX_FILE = _INDEX_DIR / "index.faiss"
_METADATA_FILE = _INDEX_DIR / "metadata.json"
_lock = asyncio.Lock()


def _api_url(settings: Settings, path: str) -> str:
    base = settings.mistral_base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}{path}"
    return f"{base}/v1{path}"


def _chunk_page(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if boundary > start + int(chunk_size * 0.55):
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _store_paths(settings: Settings) -> tuple[Path, Path]:
    directory = Path(settings.rag_index_dir)
    return directory / "index.faiss", directory / "metadata.json"


def _load_store(settings: Settings) -> tuple[faiss.IndexFlatIP | None, list[dict[str, Any]]]:
    index_file, metadata_file = _store_paths(settings)
    if not index_file.exists() or not metadata_file.exists():
        return None, []
    index = faiss.read_index(str(index_file))
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    return index, metadata


def _save_store(index: faiss.IndexFlatIP, metadata: list[dict[str, Any]], settings: Settings) -> None:
    index_file, metadata_file = _store_paths(settings)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_index = index_file.with_suffix(".tmp")
    tmp_meta = metadata_file.with_suffix(".tmp")
    faiss.write_index(index, str(tmp_index))
    tmp_meta.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp_index, index_file)
    os.replace(tmp_meta, metadata_file)


async def _embed(texts: list[str], settings: Settings) -> list[list[float]]:
    if not settings.is_mistral_configured:
        raise RuntimeError("MISTRAL_API_KEY is not configured")
    vectors: list[list[float]] = []
    async with httpx.AsyncClient(timeout=settings.rag_embedding_timeout_seconds) as client:
        # Keep requests reasonably sized for large documents.
        for start in range(0, len(texts), settings.rag_embedding_batch_size):
            batch = texts[start : start + settings.rag_embedding_batch_size]
            response = await client.post(
                _api_url(settings, "/embeddings"),
                headers={"Authorization": f"Bearer {settings.mistral_api_key}"},
                json={"model": settings.rag_embedding_model, "input": batch},
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            if len(data) != len(batch):
                raise RuntimeError("Embedding service returned an incomplete response")
            vectors.extend(item["embedding"] for item in sorted(data, key=lambda x: x["index"]))
    return vectors


async def index_ocr_result(result: OcrSuccessResponse, settings: Settings) -> dict[str, Any]:
    chunks: list[str] = []
    metadata: list[dict[str, Any]] = []
    document_id = str(uuid.uuid4())

    for page in result.page_contents:
        for chunk_index, chunk in enumerate(
            _chunk_page(
                page.plain_text or page.markdown,
                settings.rag_chunk_size,
                settings.rag_chunk_overlap,
            )
        ):
            chunks.append(chunk)
            metadata.append(
                {
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "filename": result.filename,
                    "page": page.index + 1,
                    "chunk": chunk_index + 1,
                    "text": chunk,
                }
            )

    if not chunks:
        raise ValueError("No text was available to index")

    vectors = np.asarray(await _embed(chunks, settings), dtype="float32")
    faiss.normalize_L2(vectors)

    async with _lock:
        index, existing_metadata = _load_store(settings)
        if index is None:
            index = faiss.IndexFlatIP(vectors.shape[1])
        elif index.d != vectors.shape[1]:
            raise RuntimeError("Existing RAG index uses a different embedding dimension")
        index.add(vectors)
        existing_metadata.extend(metadata)
        _save_store(index, existing_metadata, settings)

    return {
        "document_id": document_id,
        "filename": result.filename,
        "pages": result.pages,
        "chunks": len(chunks),
    }


async def retrieve(query: str, settings: Settings) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return []
    vectors = np.asarray(await _embed([query], settings), dtype="float32")
    faiss.normalize_L2(vectors)

    async with _lock:
        index, metadata = _load_store(settings)
        if index is None or not metadata:
            return []
        scores, indices = index.search(vectors, min(settings.rag_top_k, index.ntotal))

    results: list[dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        if float(score) < settings.rag_similarity_threshold:
            continue
        item = dict(metadata[idx])
        item["score"] = round(float(score), 4)
        results.append(item)
    return results


async def answer_query(query: str, settings: Settings) -> dict[str, Any]:
    sources = await retrieve(query, settings)
    if not sources:
        return {
            "answer": "I couldn't find the answer in the uploaded documents.",
            "sources": [],
            "found": False,
        }

    context = "\n\n".join(
        f"[Source {i + 1} | {s['filename']} | page {s['page']}]\n{s['text']}"
        for i, s in enumerate(sources)
    )
    system = (
        "You answer questions strictly from the supplied document context. "
        "Do not use outside knowledge or invent facts. If the context does not "
        "contain enough information to answer the question, say that the answer "
        "cannot be found in the uploaded documents. Cite supporting sources in "
        "the form [filename, page N] when making factual claims."
    )
    user = f"DOCUMENT CONTEXT:\n{context}\n\nQUESTION:\n{query}"

    async with httpx.AsyncClient(timeout=settings.rag_chat_timeout_seconds) as client:
        response = await client.post(
            _api_url(settings, "/chat/completions"),
            headers={"Authorization": f"Bearer {settings.mistral_api_key}"},
            json={
                "model": settings.rag_chat_model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()

    answer = (
        payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        or "I couldn't generate an answer from the uploaded documents."
    )
    return {
        "answer": answer,
        "found": True,
        "sources": [
            {
                "filename": s["filename"],
                "page": s["page"],
                "score": s["score"],
                "snippet": s["text"][:300],
            }
            for s in sources
        ],
    }
