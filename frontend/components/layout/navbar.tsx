"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { ScanText, Mic, Settings as SettingsIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { GithubIcon } from "@/components/common/icons";
import { APP_NAME, GITHUB_URL, NAV_LINKS } from "@/lib/constants";
import { ThemeToggle } from "@/components/common/theme-toggle";
import { buttonVariants } from "@/components/ui/button";

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-background/70 backdrop-blur-md supports-backdrop-filter:bg-background/60">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-base font-semibold tracking-tight"
        >
          <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground text-sm font-bold">
            M
          </span>
          <span className="hidden sm:inline">{APP_NAME}</span>
        </Link>

        <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "relative px-3 py-2 text-sm font-medium transition-colors duration-150",
                  active
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {link.label}
                {active && (
                  <motion.span
                    layoutId="nav-underline"
                    className="absolute inset-x-2 -bottom-px h-px bg-primary"
                    transition={{ duration: 0.25, ease: "easeOut" }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-1.5">
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View on GitHub"
            className={buttonVariants({ variant: "ghost", size: "icon" })}
          >
            <GithubIcon className="size-4" />
          </a>
          <Link
            href="/settings"
            aria-label="Settings"
            className={cn(
              buttonVariants({ variant: "ghost", size: "icon" }),
              "hidden md:inline-flex"
            )}
          >
            <SettingsIcon className="size-4" />
          </Link>
          <ThemeToggle />
        </div>
      </div>

      <MobileTabBar pathname={pathname} />
    </header>
  );
}

function MobileTabBar({ pathname }: { pathname: string }) {
  const items = [
    { href: "/", label: "Home", icon: null },
    { href: "/ocr", label: "OCR", icon: ScanText },
    { href: "/speech", label: "Speech", icon: Mic },
    { href: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-border bg-background/95 backdrop-blur-md md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      aria-label="Primary"
    >
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex min-h-12 min-w-12 flex-1 flex-col items-center justify-center gap-0.5 py-2 text-xs transition-colors duration-150",
              active ? "text-primary" : "text-muted-foreground"
            )}
          >
            {Icon ? <Icon className="size-5" /> : (
              <span className="flex size-5 items-center justify-center rounded-sm bg-current/20 text-[10px] font-bold">
                M
              </span>
            )}
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
