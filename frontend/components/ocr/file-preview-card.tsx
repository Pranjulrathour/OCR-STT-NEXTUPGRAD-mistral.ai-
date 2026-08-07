"use client";

import * as React from "react";
import { FileText, X, RefreshCw, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatBytes } from "@/lib/utils";

interface FilePreviewCardProps {
  file: File;
  isSubmitting: boolean;
  onRemove: () => void;
  onReplace: (file: File) => void;
  onExtract: () => void;
}

export function FilePreviewCard({
  file,
  isSubmitting,
  onRemove,
  onReplace,
  onExtract,
}: FilePreviewCardProps) {
  const replaceInputRef = React.useRef<HTMLInputElement>(null);

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-button bg-primary/10 text-primary">
            <FileText className="size-5" />
          </div>
          <div className="min-w-0">
            <p className="truncate font-medium text-foreground">{file.name}</p>
            <p className="text-small text-muted-foreground">
              {formatBytes(file.size)} · {file.type || "unknown type"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" aria-label="Remove file" onClick={onRemove}>
            <X className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Replace file"
            onClick={() => replaceInputRef.current?.click()}
          >
            <RefreshCw className="size-4" />
          </Button>
          <input
            ref={replaceInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
            className="sr-only"
            onChange={(e) => {
              const next = e.target.files?.[0];
              if (next) onReplace(next);
            }}
          />
          <Button onClick={onExtract} disabled={isSubmitting}>
            Extract Text
            <ArrowRight className="size-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
