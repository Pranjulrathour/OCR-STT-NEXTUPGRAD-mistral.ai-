import type { Metadata } from "next";

import { OcrView } from "@/components/ocr/ocr-view";

export const metadata: Metadata = { title: "OCR" };

export default function OcrPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <div className="mb-8 space-y-1.5">
        <h1 className="text-h2 font-bold text-foreground">OCR</h1>
        <p className="text-body text-muted-foreground">
          Extract text from images, PDFs, and scanned documents.
        </p>
      </div>

      <OcrView />
    </div>
  );
}
