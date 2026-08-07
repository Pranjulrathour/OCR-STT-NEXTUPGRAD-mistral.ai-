export interface OcrPage {
  index: number;
  markdown: string;
  plain_text: string;
}

export interface OcrResultFields {
  filename: string;
  pages: number;
  markdown: string;
  plain_text: string;
  processing_time: number;
  model: string;
  page_contents: OcrPage[];
}

export type OcrOutputTab = "markdown" | "plain_text";

export type OcrStage =
  | "idle"
  | "selected"
  | "uploading"
  | "extracting"
  | "done"
  | "error";

export interface OcrProgress {
  pagesDone: number;
  totalPages: number;
  completedPages: number[];
}

export type OcrLiveMessage =
  | { total_pages: number }
  | { pages_done: number; total_pages: number; completed_pages: number[] }
  | { result: OcrResultFields }
  | { error: string };
