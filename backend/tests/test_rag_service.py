"""RAG service tests — chunking, dedupe, document scoping, and deletion.

Embeddings are faked with a deterministic bag-of-words vectoriser rather than
random noise, so cosine similarity is *meaningful*: a query sharing words with a
chunk genuinely scores higher. That is what makes the scoping and threshold
assertions below test real behaviour instead of coincidence.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.exceptions import MistralServiceError
from app.services import rag
from app.services.mistral_ocr import OcrPage, OcrResult

_VOCAB = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta")


def _vectorise(text: str) -> list[float]:
    lowered = text.lower()
    # Trailing constant keeps every vector non-zero so L2 normalisation is safe.
    return [float(lowered.count(word)) for word in _VOCAB] + [0.25]


class FakeRagClient:
    """Stands in for the Mistral SDK client: embeddings + chat."""

    def __init__(self) -> None:
        self.embed_batches: list[list[str]] = []
        self.chat_calls: list[list[object]] = []
        self.chat_reply = "A grounded answer."
        self.embeddings = SimpleNamespace(create_async=self._embed)
        self.chat = SimpleNamespace(complete_async=self._chat)

    async def _embed(self, *, model: str, inputs: list[str]):
        self.embed_batches.append(list(inputs))
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=i, embedding=_vectorise(text))
                for i, text in enumerate(inputs)
            ]
        )

    async def _chat(self, *, model, messages, temperature=None, **kwargs):
        self.chat_calls.append(list(messages))
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.chat_reply))]
        )


@pytest.fixture
def fake_rag_client(monkeypatch: pytest.MonkeyPatch) -> FakeRagClient:
    client = FakeRagClient()
    monkeypatch.setattr("app.services.rag.get_mistral_client", lambda: client)
    return client


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Settings pinned to a throwaway index dir, ignoring any real .env."""
    rag.reset_cache()
    yield Settings(
        _env_file=None,
        mistral_api_key="test-key",
        rag_index_dir=str(tmp_path / "index"),
        rag_chunk_size=200,
        rag_chunk_overlap=20,
        rag_similarity_threshold=0.1,
        rag_top_k=5,
    )
    rag.reset_cache()


def make_document(filename: str, pages: list[str]) -> OcrResult:
    return OcrResult(
        filename=filename,
        pages=len(pages),
        markdown="\n\n".join(pages),
        plain_text="\n\n".join(pages),
        processing_time=0.1,
        model="mistral-ocr-latest",
        page_contents=[
            OcrPage(index=i, markdown=text, plain_text=text)
            for i, text in enumerate(pages)
        ],
    )


# --------------------------------------------------------------------------
# chunk_page
# --------------------------------------------------------------------------


def test_chunk_page_returns_nothing_for_blank_input() -> None:
    assert rag.chunk_page("", 100, 10) == []
    assert rag.chunk_page("   \n\t ", 100, 10) == []


def test_chunk_page_keeps_short_text_whole() -> None:
    assert rag.chunk_page("a short page", 100, 10) == ["a short page"]


def test_chunk_page_normalises_whitespace() -> None:
    assert rag.chunk_page("one\n\n  two\tthree", 100, 10) == ["one two three"]


def test_chunk_page_covers_all_text_and_overlaps() -> None:
    text = ". ".join(f"sentence number {i} padding words here" for i in range(40))
    chunks = rag.chunk_page(text, 200, 40)

    assert len(chunks) > 1
    assert all(len(chunk) <= 200 for chunk in chunks)
    # Every chunk carries content, and the first/last of the source survive.
    assert all(chunk.strip() for chunk in chunks)
    assert "sentence number 0" in chunks[0]
    assert "sentence number 39" in chunks[-1]


def test_chunk_page_makes_forward_progress_without_boundaries() -> None:
    # No ". " or newline anywhere: the boundary search finds nothing and the
    # loop must still terminate rather than spin on the same window.
    chunks = rag.chunk_page("x" * 1000, 100, 30)
    assert len(chunks) >= 10
    assert "".join(chunks).count("x") >= 1000


def test_chunk_page_clamps_overlap_that_would_stall() -> None:
    # overlap >= chunk_size would otherwise mean start never advances.
    chunks = rag.chunk_page("y" * 500, 50, 500)
    assert len(chunks) >= 10


def test_chunk_page_rejects_non_positive_chunk_size() -> None:
    with pytest.raises(ValueError):
        rag.chunk_page("some text", 0, 0)


# --------------------------------------------------------------------------
# indexing, dedupe, scoping
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_index_document_persists_chunks(fake_rag_client, settings) -> None:
    document = make_document("alpha.pdf", ["alpha alpha beta", "gamma delta"])
    indexed = await rag.index_document(document, settings)

    assert indexed.chunks == 2
    assert indexed.pages == 2
    assert indexed.deduplicated is False
    assert indexed.document_id


@pytest.mark.asyncio
async def test_reindexing_identical_content_is_deduplicated(
    fake_rag_client, settings
) -> None:
    document = make_document("alpha.pdf", ["alpha beta gamma"])

    first = await rag.index_document(document, settings)
    calls_after_first = len(fake_rag_client.embed_batches)
    second = await rag.index_document(document, settings)

    assert second.document_id == first.document_id
    assert second.deduplicated is True
    assert second.chunks == first.chunks
    # The whole point: no second round of paid embedding calls.
    assert len(fake_rag_client.embed_batches) == calls_after_first


@pytest.mark.asyncio
async def test_different_content_gets_a_different_id(fake_rag_client, settings) -> None:
    first = await rag.index_document(make_document("a.pdf", ["alpha"]), settings)
    second = await rag.index_document(make_document("b.pdf", ["beta"]), settings)
    assert first.document_id != second.document_id


@pytest.mark.asyncio
async def test_retrieval_is_scoped_to_the_requested_document(
    fake_rag_client, settings
) -> None:
    secret = await rag.index_document(
        make_document("confidential.pdf", ["alpha alpha alpha"]), settings
    )
    public = await rag.index_document(
        make_document("public.pdf", ["beta beta beta"]), settings
    )

    # A query whose words only appear in the *other* document must never reach
    # it. It may legitimately return nothing (the similarity floor rejects the
    # scoped document's own weak match) — what it must never do is leak.
    hits = await rag.retrieve("alpha", public.document_id, settings)
    assert "confidential.pdf" not in [hit.filename for hit in hits]

    # Each document is still fully searchable within its own scope.
    assert [
        h.filename for h in await rag.retrieve("beta", public.document_id, settings)
    ] == ["public.pdf"]
    assert [
        h.filename for h in await rag.retrieve("alpha", secret.document_id, settings)
    ] == ["confidential.pdf"]


@pytest.mark.asyncio
async def test_retrieve_requires_a_document_id(fake_rag_client, settings) -> None:
    await rag.index_document(make_document("a.pdf", ["alpha"]), settings)
    assert await rag.retrieve("alpha", "", settings) == []


@pytest.mark.asyncio
async def test_retrieve_ignores_blank_queries(fake_rag_client, settings) -> None:
    indexed = await rag.index_document(make_document("a.pdf", ["alpha"]), settings)
    assert await rag.retrieve("   ", indexed.document_id, settings) == []


@pytest.mark.asyncio
async def test_retrieve_on_unknown_document_returns_nothing(
    fake_rag_client, settings
) -> None:
    await rag.index_document(make_document("a.pdf", ["alpha"]), settings)
    assert await rag.retrieve("alpha", "no-such-document", settings) == []


@pytest.mark.asyncio
async def test_similarity_threshold_filters_weak_matches(
    fake_rag_client, tmp_path
) -> None:
    rag.reset_cache()
    strict = Settings(
        _env_file=None,
        mistral_api_key="test-key",
        rag_index_dir=str(tmp_path / "strict"),
        rag_similarity_threshold=0.99,
    )
    indexed = await rag.index_document(make_document("a.pdf", ["alpha beta"]), strict)
    # "zeta" shares no vocabulary with the chunk, so it cannot clear 0.99.
    assert await rag.retrieve("zeta", indexed.document_id, strict) == []
    rag.reset_cache()


# --------------------------------------------------------------------------
# deletion
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_document_removes_only_that_document(
    fake_rag_client, settings
) -> None:
    doomed = await rag.index_document(
        make_document("doomed.pdf", ["alpha alpha"]), settings
    )
    keeper = await rag.index_document(
        make_document("keeper.pdf", ["beta beta"]), settings
    )

    removed = await rag.delete_document(doomed.document_id, settings)
    assert removed == doomed.chunks

    assert await rag.retrieve("alpha", doomed.document_id, settings) == []
    # The survivor's rows must still line up with its metadata after compaction.
    survivors = await rag.retrieve("beta", keeper.document_id, settings)
    assert [hit.filename for hit in survivors] == ["keeper.pdf"]


@pytest.mark.asyncio
async def test_delete_unknown_document_is_a_no_op(fake_rag_client, settings) -> None:
    await rag.index_document(make_document("a.pdf", ["alpha"]), settings)
    assert await rag.delete_document("nope", settings) == 0


@pytest.mark.asyncio
async def test_deleted_content_can_be_reindexed(fake_rag_client, settings) -> None:
    document = make_document("a.pdf", ["alpha beta"])
    first = await rag.index_document(document, settings)
    await rag.delete_document(first.document_id, settings)

    again = await rag.index_document(document, settings)
    assert again.deduplicated is False
    assert again.chunks == first.chunks


# --------------------------------------------------------------------------
# persistence
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_index_survives_a_cold_cache(fake_rag_client, settings) -> None:
    indexed = await rag.index_document(
        make_document("a.pdf", ["alpha gamma"]), settings
    )

    rag.reset_cache()  # simulate a process restart against the same directory

    hits = await rag.retrieve("alpha", indexed.document_id, settings)
    assert [hit.filename for hit in hits] == ["a.pdf"]


@pytest.mark.asyncio
async def test_corrupt_metadata_is_discarded_not_fatal(
    fake_rag_client, settings
) -> None:
    await rag.index_document(make_document("a.pdf", ["alpha"]), settings)
    index_file, metadata_file = rag._store_paths(settings)
    metadata_file.write_text("{not json", encoding="utf-8")
    rag.reset_cache()

    # Retrieval degrades to "nothing indexed" rather than raising.
    assert await rag.retrieve("alpha", "anything", settings) == []
    assert index_file.exists()


@pytest.mark.asyncio
async def test_length_mismatch_is_rejected(fake_rag_client, settings) -> None:
    indexed = await rag.index_document(
        make_document("a.pdf", ["alpha", "beta"]), settings
    )
    _, metadata_file = rag._store_paths(settings)
    # Drop a record so metadata and vectors disagree — serving this would
    # attribute one chunk's text to another chunk's citation.
    import json

    payload = json.loads(metadata_file.read_text(encoding="utf-8"))
    payload["records"] = payload["records"][:1]
    metadata_file.write_text(json.dumps(payload), encoding="utf-8")
    rag.reset_cache()

    assert await rag.retrieve("alpha", indexed.document_id, settings) == []


# --------------------------------------------------------------------------
# answering
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_answer_query_short_circuits_without_sources(
    fake_rag_client, settings
) -> None:
    result = await rag.answer_query("alpha", "unknown-document", settings)

    assert result.found is False
    assert result.sources == []
    # No sources means no reason to spend a chat call.
    assert fake_rag_client.chat_calls == []


@pytest.mark.asyncio
async def test_answer_query_grounds_on_retrieved_chunks(
    fake_rag_client, settings
) -> None:
    indexed = await rag.index_document(
        make_document("a.pdf", ["alpha beta gamma"]), settings
    )
    result = await rag.answer_query("alpha", indexed.document_id, settings)

    assert result.found is True
    assert result.answer == "A grounded answer."
    assert [source.filename for source in result.sources] == ["a.pdf"]

    system, user = fake_rag_client.chat_calls[0]
    assert "untrusted" in system.content.lower()
    assert "alpha beta gamma" in user.content


@pytest.mark.asyncio
async def test_answer_query_reports_still_indexing(
    fake_rag_client, settings, monkeypatch
) -> None:
    monkeypatch.setattr(rag, "is_indexing", lambda document_id: True)
    result = await rag.answer_query("alpha", "pending-doc", settings)

    assert result.found is False
    assert "still being indexed" in result.answer


@pytest.mark.asyncio
async def test_empty_document_raises(fake_rag_client, settings) -> None:
    with pytest.raises(ValueError):
        await rag.index_document(make_document("blank.pdf", ["   "]), settings)


@pytest.mark.asyncio
async def test_missing_api_key_surfaces_as_service_error(settings, tmp_path) -> None:
    rag.reset_cache()
    unconfigured = Settings(
        _env_file=None,
        mistral_api_key="",
        rag_index_dir=str(tmp_path / "unconfigured"),
    )
    with pytest.raises(MistralServiceError):
        await rag.index_document(make_document("a.pdf", ["alpha"]), unconfigured)
    rag.reset_cache()


# --------------------------------------------------------------------------
# background indexing
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_schedule_indexing_returns_the_id_before_indexing_finishes(
    fake_rag_client, settings
) -> None:
    document = make_document("a.pdf", ["alpha beta"])

    document_id = rag.schedule_indexing(document, settings)
    assert document_id == rag.document_id_for(document, settings)
    assert rag.is_indexing(document_id) is True

    await rag.drain_pending()

    assert rag.is_indexing(document_id) is False
    hits = await rag.retrieve("alpha", document_id, settings)
    assert [hit.filename for hit in hits] == ["a.pdf"]


@pytest.mark.asyncio
async def test_embedding_batches_run_concurrently(fake_rag_client, tmp_path) -> None:
    rag.reset_cache()
    batched = Settings(
        _env_file=None,
        mistral_api_key="test-key",
        rag_index_dir=str(tmp_path / "batched"),
        rag_chunk_size=50,
        rag_chunk_overlap=0,
        rag_embedding_batch_size=1,
        rag_embedding_concurrency=4,
    )

    in_flight = 0
    peak = 0
    original = fake_rag_client._embed

    async def counting_embed(*, model: str, inputs: list[str]):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        try:
            await asyncio.sleep(0.01)
            return await original(model=model, inputs=inputs)
        finally:
            in_flight -= 1

    fake_rag_client.embeddings.create_async = counting_embed

    pages = [f"alpha beta page {i} words to force a chunk each" for i in range(8)]
    await rag.index_document(make_document("book.pdf", pages), batched)

    assert peak > 1, "embedding batches ran serially"
    rag.reset_cache()
