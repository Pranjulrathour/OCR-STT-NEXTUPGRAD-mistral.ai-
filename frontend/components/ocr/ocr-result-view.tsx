"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Download, FileDown, RotateCcw, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { countWords, estimateReadingMinutes } from "@/lib/utils";
import type { OcrOutputTab, OcrResultFields } from "@/types/ocr";

import { BookReader } from "./book-reader";

function downloadFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function baseName(filename: string): string {
  return filename.replace(/\.[^./]+$/, "");
}

interface OcrResultViewProps {
  result: OcrResultFields;
  onClear: () => void;
  onNewUpload: () => void;
}

export function OcrResultView({ result, onClear, onNewUpload }: OcrResultViewProps) {
  const [activeTab, setActiveTab] = React.useState<OcrOutputTab>("markdown");

  const words = countWords(result.plain_text);
  const characters = result.plain_text.length;
  const readingMinutes = estimateReadingMinutes(words);

  const activeContent = activeTab === "markdown" ? result.markdown : result.plain_text;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(activeContent);
    toast.success("Copied successfully.");
  };

  const handleDownload = (format: "txt" | "md") => {
    const suffix = format === "txt" ? "_extracted.txt" : "_extracted.md";
    downloadFile(
      `${baseName(result.filename)}${suffix}`,
      format === "txt" ? result.plain_text : result.markdown,
      format === "txt" ? "text/plain" : "text/markdown"
    );
    toast.success("Downloaded.");
  };

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-medium text-foreground">{result.filename}</p>
            <p className="text-small text-muted-foreground">Model: {result.model}</p>
          </div>
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger render={<Button variant="ghost" size="icon" onClick={handleCopy} />}>
                <Copy className="size-4" />
              </TooltipTrigger>
              <TooltipContent>Copy (Ctrl+C)</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger
                render={<Button variant="ghost" size="icon" onClick={() => handleDownload("txt")} />}
              >
                <Download className="size-4" />
              </TooltipTrigger>
              <TooltipContent>Download TXT</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger
                render={<Button variant="ghost" size="icon" onClick={() => handleDownload("md")} />}
              >
                <FileDown className="size-4" />
              </TooltipTrigger>
              <TooltipContent>Download Markdown</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger render={<Button variant="ghost" size="icon" onClick={onClear} />}>
                <Trash2 className="size-4" />
              </TooltipTrigger>
              <TooltipContent>Clear result</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger render={<Button variant="outline" size="icon" onClick={onNewUpload} />}>
                <RotateCcw className="size-4" />
              </TooltipTrigger>
              <TooltipContent>New upload</TooltipContent>
            </Tooltip>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-small text-muted-foreground sm:grid-cols-4">
          <Stat label="Pages" value={result.pages} />
          <Stat label="Words" value={words} />
          <Stat label="Characters" value={characters} />
          <Stat label="Reading Time" value={`${readingMinutes} min`} />
        </div>
      </CardHeader>

      <CardContent>
        {result.pages > 1 ? (
          <BookReader pages={result.page_contents} />
        ) : (
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as OcrOutputTab)}>
            <TabsList>
              <TabsTrigger value="markdown">Markdown</TabsTrigger>
              <TabsTrigger value="plain_text">Plain Text</TabsTrigger>
            </TabsList>
            <TabsContent value="markdown">
              <div className="max-h-[480px] overflow-y-auto rounded-input border border-border bg-muted/30 p-4">
                <article className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.markdown}</ReactMarkdown>
                </article>
              </div>
            </TabsContent>
            <TabsContent value="plain_text">
              <pre className="max-h-[480px] overflow-y-auto whitespace-pre-wrap rounded-input border border-border bg-muted/30 p-4 font-mono text-small text-foreground">
                {result.plain_text}
              </pre>
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-caption uppercase tracking-wide text-muted-foreground/70">{label}</p>
      <p className="font-medium text-foreground">{value}</p>
    </div>
  );
}
