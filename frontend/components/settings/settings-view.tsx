"use client";

import * as React from "react";
import { Monitor, Moon, Sun } from "lucide-react";

import { useTheme } from "@/hooks/useTheme";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getHealth } from "@/services/health.service";
import { APP_DESCRIPTION, APP_VERSION, GITHUB_URL } from "@/lib/constants";

const THEME_OPTIONS = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
] as const;

type ApiState = "checking" | "online" | "offline";

export function SettingsView() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  const [apiState, setApiState] = React.useState<ApiState>("checking");
  const [apiVersion, setApiVersion] = React.useState<string | null>(null);

  React.useEffect(() => setMounted(true), []);

  React.useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal).then((result) => {
      if (result.ok) {
        setApiState("online");
        setApiVersion(result.data.version);
      } else {
        setApiState("offline");
      }
    });
    return () => controller.abort();
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
          <CardDescription>
            Choose how Mistral AI Workspace looks on this device.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
            <Button
              key={value}
              variant={mounted && theme === value ? "default" : "outline"}
              size="sm"
              onClick={() => setTheme(value)}
            >
              <Icon className="size-4" />
              {label}
            </Button>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Status</CardTitle>
          <CardDescription>Connectivity to the backend service.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2">
          {apiState === "checking" && <Badge variant="neutral">Checking…</Badge>}
          {apiState === "online" && (
            <Badge variant="success">Connected{apiVersion ? ` · v${apiVersion}` : ""}</Badge>
          )}
          {apiState === "offline" && <Badge variant="destructive">Unavailable</Badge>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
          <CardDescription>{APP_DESCRIPTION}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-small text-muted-foreground">
          <p>Version {APP_VERSION}</p>
          <p>Made by Pranjul Rathour</p>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-primary hover:underline"
          >
            View source on GitHub
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
