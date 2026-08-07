"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ScanText, Mic } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { FeatureCard } from "@/components/common/feature-card";
import { GithubIcon } from "@/components/common/icons";
import { GITHUB_URL } from "@/lib/constants";

export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6">
      <section className="flex flex-col items-center gap-6 py-20 text-center sm:py-28">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1 text-small text-muted-foreground"
        >
          Powered by Mistral AI
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut", delay: 0.05 }}
          className="max-w-3xl text-h2 font-bold tracking-tight text-foreground sm:text-hero"
        >
          Transform Documents &amp; Speech Into Text
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut", delay: 0.1 }}
          className="max-w-xl text-body-lg text-muted-foreground"
        >
          Fast. Beautiful. Production ready.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut", delay: 0.15 }}
          className="flex flex-col items-center gap-3 sm:flex-row"
        >
          <Link href="/ocr" className={buttonVariants({ size: "lg" })}>
            Start Using
            <ArrowRight className="size-4" />
          </Link>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className={buttonVariants({ size: "lg", variant: "outline" })}
          >
            <GithubIcon className="size-4" />
            View GitHub
          </a>
        </motion.div>
      </section>

      <section className="grid gap-6 pb-24 sm:grid-cols-2">
        <FeatureCard
          href="/ocr"
          icon={ScanText}
          title="OCR"
          description="Extract text from images, PDFs, and scanned documents."
          points={["Images", "PDFs", "Scanned Documents"]}
        />
        <FeatureCard
          href="/speech"
          icon={Mic}
          title="Speech"
          description="Realtime speech, streaming, live transcript."
          points={["Realtime Speech", "Streaming", "Live Transcript"]}
        />
      </section>
    </div>
  );
}
