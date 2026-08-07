"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { OcrPage } from "@/types/ocr";

interface TocEntry {
  pageIndex: number;
  level: number;
  text: string;
}

function extractToc(pages: OcrPage[]): TocEntry[] {
  const entries: TocEntry[] = [];
  for (const page of pages) {
    for (const line of page.markdown.split("\n")) {
      const match = /^(#{1,3})\s+(.+)$/.exec(line.trim());
      if (match) {
        entries.push({
          pageIndex: page.index,
          level: match[1].length,
          text: match[2].trim(),
        });
      }
    }
  }
  return entries;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightMatches(text: string, query: string): React.ReactNode {
  if (!query.trim()) return text;
  const parts = text.split(new RegExp(`(${escapeRegExp(query)})`, "gi"));
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase() ? (
      <mark key={i} className="rounded-sm bg-warning/40 text-foreground">
        {part}
      </mark>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}

interface BookReaderProps {
  pages: OcrPage[];
}

export function BookReader({ pages }: BookReaderProps) {
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [query, setQuery] = React.useState("");
  const [viewMode, setViewMode] = React.useState<"markdown" | "plain_text">("markdown");

  const toc = React.useMemo(() => extractToc(pages), [pages]);

  const matchingPages = React.useMemo(() => {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return null;
    return pages
      .map((page) => ({
        page,
        count: page.plain_text.toLowerCase().split(trimmed).length - 1,
      }))
      .filter((entry) => entry.count > 0);
  }, [pages, query]);

  React.useEffect(() => {
    if (query.trim()) setViewMode("plain_text");
  }, [query]);

  const goTo = React.useCallback(
    (index: number) => {
      setCurrentIndex(Math.max(0, Math.min(pages.length - 1, index)));
    },
    [pages.length]
  );

  const currentPage = pages[currentIndex];
  if (!currentPage) return null;

  const sidebarEntries = matchingPages ?? pages.map((page) => ({ page, count: 0 }));

  return (
    <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
      <aside className="space-y-4">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search in book…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-8"
          />
        </div>

        <div className="max-h-[420px] overflow-y-auto rounded-card border border-border">
          {sidebarEntries.map(({ page, count }) => (
            <button
              key={page.index}
              type="button"
              onClick={() => goTo(page.index)}
              className={cn(
                "flex w-full items-center justify-between px-3 py-2 text-left text-small transition-colors duration-150 hover:bg-muted",
                currentIndex === page.index && "bg-muted font-medium text-foreground"
              )}
            >
              <span>Page {page.index + 1}</span>
              {query.trim() && (
                <span className="text-caption text-muted-foreground">
                  {count} match{count === 1 ? "" : "es"}
                </span>
              )}
            </button>
          ))}
        </div>

        {toc.length > 0 && (
          <div>
            <p className="mb-1.5 text-caption font-medium uppercase tracking-wide text-muted-foreground/70">
              Contents
            </p>
            <div className="max-h-[240px] space-y-0.5 overflow-y-auto">
              {toc.map((entry, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => goTo(entry.pageIndex)}
                  style={{ paddingLeft: `${(entry.level - 1) * 12 + 8}px` }}
                  className="block w-full truncate rounded-sm py-1 text-left text-small text-muted-foreground transition-colors duration-150 hover:bg-muted hover:text-foreground"
                >
                  {entry.text}
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            onClick={() => goTo(currentIndex - 1)}
            disabled={currentIndex === 0}
          >
            <ChevronLeft className="size-4" />
            Prev
          </Button>
          <span className="text-small text-muted-foreground">
            Page {currentIndex + 1} of {pages.length}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => goTo(currentIndex + 1)}
            disabled={currentIndex === pages.length - 1}
          >
            Next
            <ChevronRight className="size-4" />
          </Button>
        </div>

        <div className="mx-auto max-w-[70ch] rounded-card border border-border bg-muted/30 p-6">
          {viewMode === "markdown" ? (
            <article className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentPage.markdown}</ReactMarkdown>
            </article>
          ) : (
            <p className="whitespace-pre-wrap text-body text-foreground">
              {highlightMatches(currentPage.plain_text, query)}
            </p>
          )}
        </div>

        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setViewMode((m) => (m === "markdown" ? "plain_text" : "markdown"))}
          >
            {viewMode === "markdown" ? "View as Plain Text" : "View as Markdown"}
          </Button>
        </div>
      </div>
    </div>
  );
}
