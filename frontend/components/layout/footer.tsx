import Link from "next/link";

import { APP_VERSION, GITHUB_URL } from "@/lib/constants";

export function Footer() {
  return (
    <footer className="mb-16 border-t border-border/60 py-8 md:mb-0">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 px-4 text-sm text-muted-foreground sm:flex-row sm:justify-between sm:px-6">
        <p>Made by Pranjul Rathour</p>
        <div className="flex items-center gap-4">
          <Link
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors duration-150 hover:text-foreground"
          >
            GitHub
          </Link>
          <span>MIT License</span>
          <span>v{APP_VERSION}</span>
        </div>
      </div>
    </footer>
  );
}
