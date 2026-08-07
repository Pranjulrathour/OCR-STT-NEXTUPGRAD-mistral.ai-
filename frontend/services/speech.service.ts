import { apiRequest, apiWsUrl } from "@/lib/api";
import type { SpeechTranscriptFields } from "@/types/speech";

/** File-upload fallback transcription (PRD §82) — used when live streaming isn't available. */
export function transcribeAudio(blob: Blob, signal?: AbortSignal) {
  const formData = new FormData();
  formData.append("audio", blob);

  return apiRequest<SpeechTranscriptFields>("/api/v1/speech/transcribe", {
    method: "POST",
    body: formData,
    signal,
    timeoutMs: 60_000,
  });
}

/**
 * Opens the live transcription WebSocket (PRD §82/§84). Returns the raw
 * socket rather than wrapping it — `useSpeech` owns the audio pipeline and
 * needs direct access to `send`/`close` and every event, so wrapping it here
 * would just mean re-exposing the same surface through another layer.
 */
export function createLiveTranscriptionSocket(): WebSocket {
  const socket = new WebSocket(apiWsUrl("/api/v1/speech/live"));
  socket.binaryType = "arraybuffer";
  return socket;
}
