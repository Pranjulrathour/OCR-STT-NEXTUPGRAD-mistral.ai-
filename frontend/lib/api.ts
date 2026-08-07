import type { ApiResponse } from "@/types/api";

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;
}

export function apiUrl(path: string): string {
  return `${getApiBaseUrl()}${path}`;
}

export function apiWsUrl(path: string): string {
  return apiUrl(path).replace(/^http/, "ws");
}

interface ApiRequestOptions extends RequestInit {
  timeoutMs?: number;
}

/**
 * Thin client the frontend never bypasses to call `fetch` directly
 * (PRD §50/§51) — every OCR/Speech call goes Component → Service → here.
 * Network/timeout/parse failures are normalized into the same
 * `{ success: false, message }` envelope the backend returns for
 * validation failures, so callers never need a try/catch for the happy path.
 */
export async function apiRequest<T>(
  path: string,
  { timeoutMs = 30_000, signal, ...init }: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  if (signal) {
    signal.addEventListener("abort", () => controller.abort());
  }

  try {
    const response = await fetch(apiUrl(path), {
      ...init,
      signal: controller.signal,
    });

    const body = await response.json().catch(() => null);

    if (!response.ok) {
      return {
        success: false,
        message: body?.message ?? "Unable to process your request. Please try again.",
      };
    }

    return body as ApiResponse<T>;
  } catch {
    if (controller.signal.aborted) {
      return { success: false, message: "Request timed out. Please try again." };
    }
    return {
      success: false,
      message: "Connection lost. Check your network and try again.",
    };
  } finally {
    clearTimeout(timeout);
  }
}
