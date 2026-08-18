"use client";

import * as React from "react";
import { Loader2, MessageCircle, Send, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { askRag } from "@/services/rag.service";
import type { RagSource } from "@/types/rag";
import { cn } from "@/lib/utils";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: RagSource[];
};

export function RagChatWidget() {
  const [open, setOpen] = React.useState(false);
  const [question, setQuestion] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [messages, setMessages] = React.useState<Message[]>([
    {
      role: "assistant",
      content:
        "Ask me anything about the uploaded documents. I will only use information found in the document index.",
    },
  ]);

  const submit = async () => {
    const value = question.trim();
    if (!value || loading) return;

    setQuestion("");
    setMessages((current) => [...current, { role: "user", content: value }]);
    setLoading(true);

    const response = await askRag(value);
    if (response.success) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } else {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.message,
        },
      ]);
    }
    setLoading(false);
  };

  return (
    <div className="fixed bottom-5 right-5 z-50">
      {open && (
        <div className="mb-3 flex h-[min(620px,calc(100vh-110px))] w-[min(390px,calc(100vw-32px))] flex-col overflow-hidden rounded-2xl border border-border bg-background shadow-2xl">
          <div className="flex items-center justify-between border-b border-border bg-muted/30 px-4 py-3">
            <div>
              <p className="text-sm font-semibold">Document Assistant</p>
              <p className="text-xs text-muted-foreground">
                Answers from uploaded documents
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Close document assistant"
              onClick={() => setOpen(false)}
            >
              <X />
            </Button>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-3">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={cn(
                  "max-w-[90%] rounded-xl px-3 py-2 text-sm",
                  message.role === "user"
                    ? "ml-auto bg-primary text-primary-foreground"
                    : "mr-auto bg-muted"
                )}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2 space-y-1 border-t border-border/50 pt-2 text-xs">
                    <p className="font-medium">Sources</p>
                    {message.sources.map((source, sourceIndex) => (
                      <p key={`${source.filename}-${source.page}-${sourceIndex}`} className="text-muted-foreground">
                        {source.filename} · page {source.page}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="mr-auto flex items-center gap-2 rounded-xl bg-muted px-3 py-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Searching documents…
              </div>
            )}
          </div>

          <div className="border-t border-border p-3">
            <div className="flex items-end gap-2">
              <Textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void submit();
                  }
                }}
                placeholder="Ask about the uploaded PDF…"
                className="min-h-10 max-h-28 resize-none"
                disabled={loading}
              />
              <Button
                size="icon"
                aria-label="Send question"
                onClick={() => void submit()}
                disabled={loading || !question.trim()}
              >
                <Send />
              </Button>
            </div>
            <p className="mt-1.5 text-[10px] text-muted-foreground">
              Enter to send · Shift+Enter for a new line
            </p>
          </div>
        </div>
      )}

      {!open && (
        <Button
          size="icon-lg"
          className="size-12 rounded-full shadow-lg"
          aria-label="Open document assistant"
          onClick={() => setOpen(true)}
        >
          <MessageCircle className="size-5" />
        </Button>
      )}
    </div>
  );
}
