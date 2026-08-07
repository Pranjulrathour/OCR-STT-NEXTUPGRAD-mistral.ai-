export interface SpeechTranscriptFields {
  transcript: string;
  language: string;
  duration: number;
  processing_time: number;
  model: string;
}

export type SpeechLiveMessage =
  | { chunk: string }
  | { language: string }
  | { error: string }
  | { model: string }
  | { status: "refining" }
  | { refined_transcript: string; language: string; model: string };

export type SpeechConnectionState =
  | "disconnected"
  | "connecting"
  | "listening"
  | "streaming"
  | "paused"
  | "stopped";

export type MicrophonePermission = "unknown" | "prompting" | "granted" | "denied";
