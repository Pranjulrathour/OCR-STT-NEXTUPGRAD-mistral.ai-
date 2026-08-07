"use client";

import { Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { OcrProgress } from "@/types/ocr";

interface ProcessingProgressProps {
  progress: OcrProgress | null;
}

// Batches complete concurrently now, not strictly in page order, so each
// square reflects whether that specific page has actually landed rather
// than a fixed left-to-right sweep — pages can (and will) light up out of
// numeric order as different batches finish.
function PageStatusGrid({
  totalPages,
  completedPages,
}: {
  totalPages: number;
  completedPages: number[];
}) {
  const done = new Set(completedPages);

  return (
    <div
      className="grid max-h-48 gap-1 overflow-y-auto rounded-md border border-border bg-background/40 p-2"
      style={{ gridTemplateColumns: "repeat(auto-fill, minmax(1.75rem, 1fr))" }}
    >
      {Array.from({ length: totalPages }, (_, index) => {
        const isDone = done.has(index);
        return (
          <div
            key={index}
            title={`Page ${index + 1}${isDone ? " — extracted" : " — pending"}`}
            className={cn(
              "flex aspect-square items-center justify-center rounded-sm text-[10px] font-medium transition-colors duration-300",
              isDone
                ? "bg-primary text-primary-foreground"
                : "animate-pulse bg-muted text-muted-foreground"
            )}
          >
            {index + 1}
          </div>
        );
      })}
    </div>
  );
}

export function ProcessingProgress({ progress }: ProcessingProgressProps) {
  const totalPages = progress?.totalPages ?? 0;
  const pagesDone = progress?.pagesDone ?? 0;
  const percent = totalPages > 0 ? Math.round((pagesDone / totalPages) * 100) : 0;
  const isMultiPage = totalPages > 1;

  return (
    <div className="flex flex-col gap-4 rounded-card border border-border bg-card p-6">
      <div className="flex items-center gap-3">
        <Loader2 className="size-5 shrink-0 animate-spin text-primary" />
        <p className="font-medium text-foreground">
          {!progress
            ? "Uploading document…"
            : isMultiPage
              ? `Extracting page ${pagesDone} of ${totalPages}…`
              : "Extracting text with Mistral OCR…"}
        </p>
      </div>
      {isMultiPage && (
        <>
          <Progress value={percent}>
            <span className="text-small text-muted-foreground">{percent}%</span>
          </Progress>
          <PageStatusGrid
            totalPages={totalPages}
            completedPages={progress?.completedPages ?? []}
          />
        </>
      )}
    </div>
  );
}
