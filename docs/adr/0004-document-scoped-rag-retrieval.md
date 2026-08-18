# ADR 0004: Scope RAG retrieval to one document, and never accept document text from a client

## Context

The document-assistant feature (PR #1) shipped a working RAG pipeline, but with
two design choices that turned out to be behavioural bugs once exercised against
the real Mistral API:

1. **One global, append-only FAISS index with no per-document filter.**
   `document_id` was written into chunk metadata but never read back, so a
   question retrieved across every document ever indexed on the host. Verified
   with two unrelated uploads: asking about the first returned the second as a
   source too. The UI said "Ask about the uploaded PDF" (singular) while actually
   answering from all of them. With no auth in the app this is a correctness and
   expectation bug; the moment two people share a deployment it is a
   data-isolation bug.
2. **`POST /rag/index` accepted a client-supplied `OcrSuccessResponse`.** The
   index was therefore populated from client input rather than server-side OCR
   state. A plain `curl` inserting invented text under the filename
   `totally_legit_policy.pdf` came back from the assistant cited and
   authoritative.

A third problem was structural rather than behavioural: indexing was awaited
*before* the OCR response returned, and `_embed` looped its batches serially — so
a 1-page image took 7.35s wall-clock against 2.86s of actual OCR, and a
1500-page document would have prepended ~125 sequential round trips to the
response.

## Decision

- **`retrieve()` requires a `document_id`** and restricts the FAISS search to
  that document's rows using `IDSelectorArray` via `SearchParameters.sel`
  (verified against `faiss-cpu==1.15`). This is an exact scoped search, not
  over-fetch-then-filter. `POST /api/v1/rag/chat` takes `document_id` as a
  required field; the frontend publishes the id of the document on screen through
  an `ActiveDocumentProvider` context and clears it on unmount.
- **No endpoint accepts document text.** `POST /rag/index` is removed. Indexing
  is a side effect of `/api/v1/ocr` and `WS /api/v1/ocr/live`, driven by
  server-side OCR output. `DELETE /api/v1/rag/documents/{document_id}` is added
  so the index is not append-only forever.
- **`document_id` is a content hash, not a uuid.** That makes the id available
  *before* embedding finishes, which is what lets `POST /ocr` schedule indexing
  in the background (`schedule_indexing`) and return immediately. It also makes
  deduplication free: identical content maps to the same id and is never
  re-embedded.
- **Embedding batches run concurrently** (`RAG_EMBEDDING_CONCURRENCY`, mirroring
  `OCR_BATCH_CONCURRENCY`), and all FAISS/JSON disk I/O moved to
  `asyncio.to_thread` with the loaded store cached in memory.

## Consequences

- **Why scoping over auth:** adding real tenancy is a much larger change, and
  scoping is both necessary regardless and sufficient to fix the observable bug.
  When auth does arrive, the `document_id` filter is the hook a per-user filter
  extends, not something to be reworked.
- **Why remove rather than harden `/rag/index`:** OCR already indexes
  automatically, so the endpoint had no remaining purpose that justified the
  attack surface. `tests/test_rag_api.py::test_no_client_facing_index_endpoint`
  asserts it stays gone.
- A content-derived id means re-uploading a file resumes the same document rather
  than creating a duplicate — good for cost, but note that a *changed* embedding
  model or chunk size intentionally produces a new id and forces a re-index,
  because the old vectors are no longer comparable.
- Chat can now be asked about a document whose background indexing has not
  finished. `answer_query` reports "still being indexed" instead of the
  misleading "couldn't find the answer".
- Background indexing is awaited during app shutdown (`drain_pending`) so a
  redeploy does not silently drop work the client was told to expect.
- **The index is a file on disk.** Any deployment that should keep it across
  restarts needs a volume at the index directory. The image declares
  `VOLUME /app/data` and creates it owned by the non-root `appuser` — without
  that `chown`, the first index write failed with `EACCES`, since `/app` is
  root-owned and the process does not run as root.

## Alternatives Considered

- **Over-fetch then filter in Python** (search top-50, keep the matching
  document's hits). Rejected: approximate, and it degrades as the corpus grows —
  a document whose chunks all rank below 50 becomes silently unsearchable.
- **One FAISS index file per document.** Rejected for now: cleaner isolation, but
  it trades one file handle and one cached store for N, and the selector approach
  already gives exact scoping. Worth revisiting if the corpus grows enough that a
  single index no longer fits comfortably in memory.
- **Keep `/rag/index` but require an auth token.** Rejected: there is no auth
  layer yet, and the endpoint is redundant with automatic OCR indexing.
- **Keep awaiting indexing so the response can report real chunk counts.**
  Rejected: it made the flagship OCR path measurably slower for a number the
  client does not need. The WebSocket path, which has already sent its result,
  does still report `rag_indexed` with the true count.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
