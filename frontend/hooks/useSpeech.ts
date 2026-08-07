"use client";

import * as React from "react";
import { toast } from "sonner";

import { createLiveTranscriptionSocket } from "@/services/speech.service";
import type {
  MicrophonePermission,
  SpeechConnectionState,
  SpeechLiveMessage,
} from "@/types/speech";

const SAMPLE_RATE = 16_000;
// Bump this whenever pcm-worklet-processor.js's message format changes.
// The browser can cache the worklet module from a prior session; without a
// cache-busting query param, a stale worklet silently keeps posting the old
// message shape, `message.type` is `undefined` on the new handler, neither
// branch matches, and audio never reaches the socket — no error, because
// there's nothing on the wire to error about, just a "Listening" state that
// never produces a single transcript chunk.
const PCM_WORKLET_VERSION = "2";

type WorkletMessage =
  | { type: "audio"; buffer: ArrayBuffer }
  | { type: "level"; value: number };

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return (
    target.tagName === "INPUT" ||
    target.tagName === "TEXTAREA" ||
    target.isContentEditable
  );
}

export function useSpeech() {
  const [permission, setPermission] = React.useState<MicrophonePermission>("unknown");
  const [connectionState, setConnectionState] =
    React.useState<SpeechConnectionState>("disconnected");
  const [transcript, setTranscript] = React.useState("");
  const [durationSeconds, setDurationSeconds] = React.useState(0);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [model, setModel] = React.useState<string | null>(null);
  const [language, setLanguage] = React.useState<string | null>(null);
  const [audioLevel, setAudioLevel] = React.useState(0);
  const [isRefining, setIsRefining] = React.useState(false);
  const [wasRefined, setWasRefined] = React.useState(false);

  const audioContextRef = React.useRef<AudioContext | null>(null);
  const workletNodeRef = React.useRef<AudioWorkletNode | null>(null);
  const sourceNodeRef = React.useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);
  const socketRef = React.useRef<WebSocket | null>(null);
  const timerRef = React.useRef<ReturnType<typeof setInterval> | null>(null);
  const pausedRef = React.useRef(false);
  const startRef = React.useRef<() => void>(() => {});
  const stopRef = React.useRef<() => void>(() => {});
  const connectionStateRef = React.useRef<SpeechConnectionState>("disconnected");
  connectionStateRef.current = connectionState;

  const stopTimer = React.useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const teardownAudio = React.useCallback(() => {
    workletNodeRef.current?.disconnect();
    sourceNodeRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      void audioContextRef.current.close();
    }
    workletNodeRef.current = null;
    sourceNodeRef.current = null;
    streamRef.current = null;
    audioContextRef.current = null;
    setAudioLevel(0);
  }, []);

  const start = React.useCallback(async () => {
    setErrorMessage(null);
    setTranscript("");
    setDurationSeconds(0);
    setLanguage(null);
    setWasRefined(false);
    setIsRefining(false);
    pausedRef.current = false;
    setConnectionState("connecting");

    let stream: MediaStream;
    try {
      setPermission("prompting");
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setPermission("granted");
    } catch {
      setPermission("denied");
      setConnectionState("disconnected");
      setErrorMessage("Microphone permission required.");
      return;
    }
    streamRef.current = stream;

    const socket = createLiveTranscriptionSocket();
    socketRef.current = socket;

    socket.onopen = () => {
      void (async () => {
        try {
          const audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
          audioContextRef.current = audioContext;
          await audioContext.audioWorklet.addModule(
            `/pcm-worklet-processor.js?v=${PCM_WORKLET_VERSION}`
          );

          const source = audioContext.createMediaStreamSource(stream);
          sourceNodeRef.current = source;
          const worklet = new AudioWorkletNode(audioContext, "pcm-worklet-processor");
          workletNodeRef.current = worklet;

          worklet.port.onmessage = (event: MessageEvent<WorkletMessage>) => {
            const message = event.data;
            if (message.type === "audio") {
              if (!pausedRef.current && socket.readyState === WebSocket.OPEN) {
                socket.send(message.buffer);
              }
            } else if (message.type === "level") {
              setAudioLevel(pausedRef.current ? 0 : Math.min(1, message.value * 4));
            }
          };

          source.connect(worklet);
          setConnectionState("listening");
          timerRef.current = setInterval(() => setDurationSeconds((d) => d + 1), 1000);
        } catch {
          setErrorMessage("Audio device unavailable.");
          socket.close();
        }
      })();
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      let payload: SpeechLiveMessage;
      try {
        payload = JSON.parse(event.data) as SpeechLiveMessage;
      } catch {
        return;
      }
      if ("chunk" in payload) {
        setTranscript((prev) => prev + payload.chunk);
        setConnectionState((s) => (s === "stopped" ? s : "streaming"));
      } else if ("refined_transcript" in payload) {
        setTranscript(payload.refined_transcript);
        setLanguage(payload.language);
        setIsRefining(false);
        setWasRefined(true);
        toast.success("Transcript refined for accuracy.");
      } else if ("status" in payload && payload.status === "refining") {
        setIsRefining(true);
      } else if ("model" in payload) {
        setModel(payload.model);
      } else if ("language" in payload) {
        setLanguage(payload.language);
      } else if ("error" in payload) {
        setErrorMessage(payload.error);
      }
    };

    socket.onerror = () => {
      setErrorMessage("Connection lost.");
    };

    socket.onclose = () => {
      stopTimer();
      teardownAudio();
      setConnectionState((s) => (s === "stopped" ? "stopped" : "disconnected"));
    };
  }, [stopTimer, teardownAudio]);

  const pause = React.useCallback(() => {
    pausedRef.current = true;
    setAudioLevel(0);
    setConnectionState("paused");
  }, []);

  const resume = React.useCallback(() => {
    pausedRef.current = false;
    setConnectionState("listening");
  }, []);

  const stop = React.useCallback(() => {
    setConnectionState("stopped");
    stopTimer();
    // Stop capturing immediately, but keep the socket open — the server
    // still needs to flush trailing transcript chunks (and run the
    // accuracy-refinement pass) before it closes the connection itself
    // (PRD §122).
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send("stop");
    }
    teardownAudio();
  }, [stopTimer, teardownAudio]);

  const clear = React.useCallback(() => {
    socketRef.current?.close();
    setTranscript("");
    setDurationSeconds(0);
    setConnectionState("disconnected");
    setErrorMessage(null);
    setLanguage(null);
    setWasRefined(false);
    setIsRefining(false);
  }, []);

  // Kept in refs so the single page-level keydown listener below always
  // calls the latest start/stop without re-subscribing on every render.
  startRef.current = () => void start();
  stopRef.current = stop;

  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code !== "Space" || event.repeat || isTypingTarget(event.target)) return;
      event.preventDefault();
      const state = connectionStateRef.current;
      if (state === "disconnected" || state === "stopped") {
        startRef.current();
      } else if (state === "listening" || state === "streaming" || state === "paused") {
        stopRef.current();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  React.useEffect(() => {
    return () => {
      socketRef.current?.close();
      stopTimer();
      teardownAudio();
    };
  }, [stopTimer, teardownAudio]);

  return {
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
  };
}
