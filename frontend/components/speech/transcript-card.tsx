"use client";

import * as React from "react";
import { Copy, Download, Loader2, Mic, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/common/empty-state";

const SCROLL_BOTTOM_THRESHOLD_PX = 48;

interface TranscriptCardProps {
  transcript: string;
  isRefining: boolean;
  onClear: () => void;
}

export function TranscriptCard({ transcript, isRefining, onClear }: TranscriptCardProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = React.useState(true);
  const [confirmOpen, setConfirmOpen] = React.useState(false);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (el && autoScroll) {
      el.scrollTop = el.scrollHeight;
    }
  }, [transcript, autoScroll]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setAutoScroll(distanceFromBottom < SCROLL_BOTTOM_THRESHOLD_PX);
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(transcript);
    toast.success("Copied successfully.");
  };

  const handleDownload = () => {
    const date = new Date().toISOString().slice(0, 10);
    const blob = new Blob([transcript], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `speech_${date}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Downloaded.");
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Live Transcript</CardTitle>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" aria-label="Copy transcript" onClick={handleCopy}>
            <Copy className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Download transcript"
            onClick={handleDownload}
          >
            <Download className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Clear transcript"
            onClick={() => setConfirmOpen(true)}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {transcript ? (
          <div
            ref={scrollRef}
            onScroll={handleScroll}
            className="max-h-[360px] overflow-y-auto rounded-input border border-border bg-muted/30 p-4"
          >
            <p className="whitespace-pre-wrap text-body text-foreground">{transcript}</p>
            {isRefining && (
              <div className="mt-2 flex items-center gap-1.5 text-small text-muted-foreground">
                <Loader2 className="size-3.5 animate-spin" />
                Refining transcript…
              </div>
            )}
          </div>
        ) : (
          <EmptyState
            icon={Mic}
            title="Press Start Recording"
            description="to begin transcription."
          />
        )}
      </CardContent>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete transcript?</DialogTitle>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                onClear();
                setConfirmOpen(false);
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
