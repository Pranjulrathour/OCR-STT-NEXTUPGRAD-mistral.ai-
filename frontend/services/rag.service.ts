import { apiRequest } from "@/lib/api";
import type { RagChatResponse } from "@/types/rag";

export function askRag(question: string) {
  return apiRequest<RagChatResponse>("/api/v1/rag/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    timeoutMs: 90_000,
  });
}
