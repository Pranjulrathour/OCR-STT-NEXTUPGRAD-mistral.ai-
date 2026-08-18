import { apiRequest } from "@/lib/api";
import type { RagChatResponse } from "@/types/rag";

/**
 * Ask a question about one specific document.
 *
 * `documentId` is not optional: the backend scopes retrieval to it, so omitting
 * it is what used to let an answer come from somebody else's upload.
 */
export function askRag(documentId: string, question: string) {
  return apiRequest<RagChatResponse>("/api/v1/rag/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, question }),
    timeoutMs: 90_000,
  });
}
