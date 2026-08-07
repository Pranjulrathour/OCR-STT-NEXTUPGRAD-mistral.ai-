import { apiUrl } from "@/lib/api";
import type { HealthStatus } from "@/types/api";

/**
 * The health endpoint intentionally returns a bare `{ status, version }`
 * object (PRD §76), not the standard success/message envelope used by
 * every other endpoint — so it bypasses `apiRequest` rather than being
 * force-fit into that shape.
 */
export async function getHealth(
  signal?: AbortSignal
): Promise<{ ok: true; data: HealthStatus } | { ok: false }> {
  try {
    const response = await fetch(apiUrl("/api/v1/health"), { signal });
    if (!response.ok) return { ok: false };
    const data = (await response.json()) as HealthStatus;
    return { ok: true, data };
  } catch {
    return { ok: false };
  }
}
