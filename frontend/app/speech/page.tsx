import type { Metadata } from "next";

import { SpeechView } from "@/components/speech/speech-view";

export const metadata: Metadata = { title: "Speech" };

export default function SpeechPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <div className="mb-8 space-y-1.5">
        <h1 className="text-h2 font-bold text-foreground">Speech</h1>
        <p className="text-body text-muted-foreground">
          Realtime speech, streaming, live transcript.
        </p>
      </div>

      <SpeechView />
    </div>
  );
}
