"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const THEME_ORDER = ["light", "dark", "system"] as const;

const THEME_ICON: Record<(typeof THEME_ORDER)[number], React.ReactNode> = {
  light: <Sun className="size-4" />,
  dark: <Moon className="size-4" />,
  system: <Monitor className="size-4" />,
};

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => setMounted(true), []);

  const current = (theme as (typeof THEME_ORDER)[number]) ?? "system";

  const cycleTheme = () => {
    const nextIndex = (THEME_ORDER.indexOf(current) + 1) % THEME_ORDER.length;
    setTheme(THEME_ORDER[nextIndex]);
  };

  if (!mounted) {
    return <div className="size-9" aria-hidden />;
  }

  return (
    <Tooltip>
      <TooltipTrigger
        render={<Button variant="ghost" size="icon" onClick={cycleTheme} />}
        aria-label={`Switch theme (current: ${current})`}
      >
        {THEME_ICON[current]}
      </TooltipTrigger>
      <TooltipContent>Theme: {current}</TooltipContent>
    </Tooltip>
  );
}
