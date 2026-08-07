"use client";

import * as React from "react";
import { UploadCloud } from "lucide-react";

import { cn } from "@/lib/utils";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
}

export function UploadDropzone({ onFileSelected }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onFileSelected(file);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      className={cn(
        "flex flex-col items-center gap-4 rounded-card border-2 border-dashed px-6 py-16 text-center transition-colors duration-200 ease-out cursor-pointer",
        isDragging
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/50 hover:bg-muted/40"
      )}
    >
      <div
        className={cn(
          "flex size-14 items-center justify-center rounded-full bg-muted text-muted-foreground transition-transform duration-200 ease-out",
          isDragging && "scale-110 text-primary"
        )}
      >
        <UploadCloud className="size-6" />
      </div>
      <div className="space-y-1">
        <p className="font-medium text-foreground">Drop a PDF or Image</p>
        <p className="text-small text-muted-foreground">
          or click to choose a file — PDF, JPG, PNG up to 20MB
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
        className="sr-only"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
}
