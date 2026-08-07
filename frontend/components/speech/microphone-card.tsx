"use client";

import { motion } from "framer-motion";
import { Mic, Pause, Play, Square } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { formatDuration } from "@/lib/utils";
import type { SpeechConnectionState } from "@/types/speech";

const STATE_LABEL: Record<SpeechConnectionState, string> = {
  disconnected: "Disconnected",
  connecting: "Connecting…",
  listening: "Listening",
  streaming: "Streaming",
  paused: "Paused",
  stopped: "Stopped",
};

const STATE_BADGE_VARIANT: Record<
  SpeechConnectionState,
  "neutral" | "info" | "success" | "warning"
> = {
  disconnected: "neutral",
  connecting: "info",
  listening: "success",
  streaming: "success",
  paused: "warning",
  stopped: "neutral",
};

interface MicrophoneCardProps {
  connectionState: SpeechConnectionState;
  durationSeconds: number;
  audioLevel: number;
  language: string | null;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
}

export function MicrophoneCard({
  connectionState,
  durationSeconds,
  audioLevel,
  language,
  onStart,
  onPause,
  onResume,
  onStop,
}: MicrophoneCardProps) {
  const isActive = connectionState === "listening" || connectionState === "streaming";
  const isPaused = connectionState === "paused";
  const isIdle = connectionState === "disconnected" || connectionState === "stopped";

  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-5 py-10">
        <div className="relative flex size-24 items-center justify-center">
          {isActive && (
            <motion.div
              aria-hidden
              className="absolute inset-0 rounded-full bg-destructive/20"
              animate={{ scale: 1 + audioLevel * 0.6 }}
              transition={{ duration: 0.08, ease: "linear" }}
            />
          )}
          <motion.div
            animate={isActive ? { scale: [1, 1.05, 1] } : { scale: 1 }}
            transition={{ duration: 1.6, repeat: isActive ? Infinity : 0, ease: "easeInOut" }}
            className={
              "relative flex size-20 items-center justify-center rounded-full " +
              (isActive
                ? "bg-destructive/10 text-destructive"
                : "bg-primary/10 text-primary")
            }
          >
            <Mic className="size-9" />
          </motion.div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={STATE_BADGE_VARIANT[connectionState]}>
            {STATE_LABEL[connectionState]}
          </Badge>
          <span className="font-mono text-body text-muted-foreground">
            {formatDuration(durationSeconds)}
          </span>
          {language && <Badge variant="neutral">{language.toUpperCase()}</Badge>}
        </div>

        <div className="flex items-center gap-2">
          {isIdle && (
            <Tooltip>
              <TooltipTrigger render={<Button size="lg" onClick={onStart} />}>
                <Mic className="size-4" />
                Start Recording
              </TooltipTrigger>
              <TooltipContent>Space</TooltipContent>
            </Tooltip>
          )}
          {isActive && (
            <Button size="lg" variant="outline" onClick={onPause}>
              <Pause className="size-4" />
              Pause
            </Button>
          )}
          {isPaused && (
            <Button size="lg" variant="outline" onClick={onResume}>
              <Play className="size-4" />
              Resume
            </Button>
          )}
          {(isActive || isPaused) && (
            <Tooltip>
              <TooltipTrigger
                render={<Button size="lg" variant="destructive" onClick={onStop} />}
              >
                <Square className="size-4" />
                Stop
              </TooltipTrigger>
              <TooltipContent>Space</TooltipContent>
            </Tooltip>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
