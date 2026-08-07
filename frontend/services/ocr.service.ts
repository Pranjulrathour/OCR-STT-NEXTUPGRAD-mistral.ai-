import { apiRequest, apiWsUrl } from "@/lib/api";
import type { OcrResultFields } from "@/types/ocr";

/**
 * Sends the file only when the caller invokes this (PRD §103 — no backend
 * call happens on file selection, only when the user clicks Extract).
 * Kept for small/quick uploads and programmatic API consumers — the UI uses
 * `createOcrLiveSocket` instead so book-scale PDFs get real progress.
 */
export function extractText(file: File, signal?: AbortSignal) {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<OcrResultFields>("/api/v1/ocr", {
    method: "POST",
    body: formData,
    signal,
    timeoutMs: 30_000,
  });
}

/**
 * Opens the live OCR WebSocket. The caller sends one JSON metadata frame
 * (`{filename, content_type}`) followed by one binary frame with the whole
 * file, then listens for `total_pages` → repeated `pages_done` → `result`
 * (or `error`) — see `useOCR` for the state machine built on top of this.
 */
export function createOcrLiveSocket(): WebSocket {
  return new WebSocket(apiWsUrl("/api/v1/ocr/live"));
}
