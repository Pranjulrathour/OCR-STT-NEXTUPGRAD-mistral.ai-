"use client";

import { MicOff } from "lucide-react";

import { ErrorBanner } from "@/components/common/error-banner";
import { useSpeech } from "@/hooks/useSpeech";

import { MicrophoneCard } from "./microphone-card";
import { StatisticsCard } from "./statistics-card";
import { TranscriptCard } from "./transcript-card";

export function SpeechView() {
  const {
    permission,
    connectionState,
    transcript,
    durationSeconds,
    errorMessage,
    model,
    language,
    audioLevel,
    isRefining,
    wasRefined,
    start,
    pause,
    resume,
    stop,
    clear,
  } = useSpeech();

  return (
    <div className="space-y-6">
      <MicrophoneCard
        connectionState={connectionState}
        durationSeconds={durationSeconds}
        audioLevel={audioLevel}
        language={language}
        onStart={start}
        onPause={pause}
        onResume={resume}
        onStop={stop}
      />

      {permission === "denied" && (
        <div className="flex flex-col items-center gap-3 rounded-card border border-warning/30 bg-warning/5 px-6 py-8 text-center">
          <MicOff className="size-6 text-warning" />
          <p className="text-body text-foreground">Microphone permission required.</p>
          <p className="text-small text-muted-foreground">
            Enable microphone access for this site in your browser&apos;s address bar or
            settings, then try again.
          </p>
        </div>
      )}

      {errorMessage && permission !== "denied" && (
        <ErrorBanner message={errorMessage} onRetry={start} />
      )}

      <TranscriptCard transcript={transcript} isRefining={isRefining} onClear={clear} />

      <StatisticsCard
        transcript={transcript}
        durationSeconds={durationSeconds}
        model={model}
        language={language}
        isRefining={isRefining}
        wasRefined={wasRefined}
      />
    </div>
  );
}
