"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";

interface FeatureCardProps {
  href: string;
  icon: LucideIcon;
  title: string;
  description: string;
  points: string[];
}

export function FeatureCard({
  href,
  icon: Icon,
  title,
  description,
  points,
}: FeatureCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      <Link
        href={href}
        className="group flex h-full flex-col gap-4 rounded-card border border-border bg-card p-6 shadow-sm transition-shadow duration-200 ease-out hover:shadow-md sm:p-8"
      >
        <div className="flex size-11 items-center justify-center rounded-button bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
        <div className="space-y-1.5">
          <h3 className="text-h4 font-semibold text-foreground">{title}</h3>
          <p className="text-body text-muted-foreground">{description}</p>
        </div>
        <ul className="space-y-1.5 text-small text-muted-foreground">
          {points.map((point) => (
            <li key={point} className="flex items-center gap-2">
              <span className="size-1 rounded-full bg-muted-foreground/60" />
              {point}
            </li>
          ))}
        </ul>
        <span className="mt-auto inline-flex items-center gap-1 text-small font-medium text-primary opacity-0 transition-opacity duration-200 ease-out group-hover:opacity-100">
          Try it now
          <ArrowRight className="size-3.5 transition-transform duration-200 ease-out group-hover:translate-x-0.5" />
        </span>
      </Link>
    </motion.div>
  );
}
