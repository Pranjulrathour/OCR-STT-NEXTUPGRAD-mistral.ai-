"use client";

import { FileText } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorBanner } from "@/components/common/error-banner";
import { useOCR } from "@/hooks/useOCR";

import { FilePreviewCard } from "./file-preview-card";
import { OcrResultView } from "./ocr-result-view";
import { ProcessingProgress } from "./processing-progress";
import { UploadDropzone } from "./upload-dropzone";

const PROCESSING_STAGES = new Set(["uploading", "extracting"]);

export function OcrView() {
  const {
    file,
    stage,
    progress,
    result,
    errorMessage,
    selectFile,
    removeFile,
    extract,
    reset,
  } = useOCR();

  if (stage === "idle") {
    return (
      <div className="space-y-6">
        <UploadDropzone onFileSelected={selectFile} />
        <EmptyState
          icon={FileText}
          title="Upload an image or PDF"
          description="to begin text extraction — even a whole book."
        />
      </div>
    );
  }

  if (stage === "selected" && file) {
    return (
      <FilePreviewCard
        file={file}
        isSubmitting={false}
        onRemove={removeFile}
        onReplace={selectFile}
        onExtract={extract}
      />
    );
  }

  if (PROCESSING_STAGES.has(stage)) {
    return <ProcessingProgress progress={progress} />;
  }

  if (stage === "error") {
    return (
      <ErrorBanner message={errorMessage ?? "Something went wrong."} onRetry={extract} />
    );
  }

  if (stage === "done" && result) {
    return <OcrResultView result={result} onClear={reset} onNewUpload={reset} />;
  }

  return null;
}
