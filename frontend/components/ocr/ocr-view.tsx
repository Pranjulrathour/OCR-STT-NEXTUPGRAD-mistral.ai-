"use client";

import * as React from "react";
import { FileText } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorBanner } from "@/components/common/error-banner";
import { useActiveDocument } from "@/components/rag/active-document";
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

  // Publish the extracted document so the assistant answers about this
  // document and nothing else. Cleared on unmount and whenever the result goes
  // away, so a stale id can never outlive what is on screen.
  const { setDocument } = useActiveDocument();
  const documentId = result?.document_id ?? null;
  const filename = result?.filename ?? null;
  React.useEffect(() => {
    setDocument(documentId && filename ? { documentId, filename } : null);
    return () => setDocument(null);
  }, [documentId, filename, setDocument]);

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
