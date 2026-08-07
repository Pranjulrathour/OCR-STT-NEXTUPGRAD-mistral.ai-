"use client";

import * as React from "react";
import { toast } from "sonner";

import { createOcrLiveSocket } from "@/services/ocr.service";
import { ACCEPTED_OCR_FILE_TYPES, MAX_OCR_FILE_SIZE_BYTES } from "@/lib/constants";
import type {
  OcrLiveMessage,
  OcrProgress,
  OcrResultFields,
  OcrStage,
} from "@/types/ocr";

// Must match `UPLOAD_CHUNK_BYTES` in backend/app/api/ocr.py — sending the
// whole file as one WS frame hit uvicorn's default 16MB max message size
// and silently broke on a real 40MB scanned book, so the file goes over
// the wire as many small frames instead of one giant one.
const UPLOAD_CHUNK_BYTES = 512 * 1024;

function validateFile(file: File): string | null {
  if (file.size === 0) return "This file is empty.";
  if (file.size > MAX_OCR_FILE_SIZE_BYTES) return "File exceeds the 100MB limit.";
  if (
    !ACCEPTED_OCR_FILE_TYPES.includes(file.type as (typeof ACCEPTED_OCR_FILE_TYPES)[number])
  ) {
    return "Only PDF, JPG, PNG are supported.";
  }
  return null;
}

export function useOCR() {
  const [file, setFile] = React.useState<File | null>(null);
  const [stage, setStage] = React.useState<OcrStage>("idle");
  const [progress, setProgress] = React.useState<OcrProgress | null>(null);
  const [result, setResult] = React.useState<OcrResultFields | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const socketRef = React.useRef<WebSocket | null>(null);

  React.useEffect(() => {
    return () => socketRef.current?.close();
  }, []);

  const selectFile = React.useCallback((candidate: File): boolean => {
    const validationError = validateFile(candidate);
    if (validationError) {
      toast.error(validationError);
      return false;
    }
    setFile(candidate);
    setStage("selected");
    setResult(null);
    setProgress(null);
    setErrorMessage(null);
    return true;
  }, []);

  const removeFile = React.useCallback(() => {
    setFile(null);
    setStage("idle");
    setResult(null);
    setProgress(null);
    setErrorMessage(null);
  }, []);

  const extract = React.useCallback(() => {
    if (!file) return;

    setStage("uploading");
    setErrorMessage(null);
    setProgress(null);

    const socket = createOcrLiveSocket();
    socketRef.current = socket;

    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          filename: file.name,
          content_type: file.type,
          size: file.size,
        })
      );
      for (let offset = 0; offset < file.size; offset += UPLOAD_CHUNK_BYTES) {
        socket.send(file.slice(offset, offset + UPLOAD_CHUNK_BYTES));
      }
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      let payload: OcrLiveMessage;
      try {
        payload = JSON.parse(event.data) as OcrLiveMessage;
      } catch {
        return;
      }
      if ("result" in payload) {
        setStage("done");
        setResult(payload.result);
      } else if ("pages_done" in payload) {
        setProgress({
          pagesDone: payload.pages_done,
          totalPages: payload.total_pages,
          completedPages: payload.completed_pages,
        });
      } else if ("total_pages" in payload) {
        setProgress({ pagesDone: 0, totalPages: payload.total_pages, completedPages: [] });
        setStage("extracting");
      } else if ("error" in payload) {
        setStage("error");
        setErrorMessage(payload.error);
      }
    };

    socket.onerror = () => {
      setStage((current) => (current === "done" ? current : "error"));
      setErrorMessage((current) => current ?? "Connection lost. Check your network and try again.");
    };

    socket.onclose = () => {
      socketRef.current = null;
    };
  }, [file]);

  const reset = React.useCallback(() => {
    socketRef.current?.close();
    setFile(null);
    setStage("idle");
    setResult(null);
    setProgress(null);
    setErrorMessage(null);
  }, []);

  return {
    file,
    stage,
    progress,
    result,
    errorMessage,
    selectFile,
    removeFile,
    extract,
    reset,
  };
}
