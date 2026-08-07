"use client";

import { Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import type { OcrProgress } from "@/types/ocr";

interface ProcessingProgressProps {
  progress: OcrProgress | null;
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
        <Progress value={percent}>
          <span className="text-small text-muted-foreground">{percent}%</span>
        </Progress>
      )}
    </div>
  );
}
