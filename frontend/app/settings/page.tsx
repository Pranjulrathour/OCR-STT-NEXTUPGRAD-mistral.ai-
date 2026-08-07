import type { Metadata } from "next";

import { SettingsView } from "@/components/settings/settings-view";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <div className="mb-8 space-y-1.5">
        <h1 className="text-h2 font-bold text-foreground">Settings</h1>
        <p className="text-body text-muted-foreground">
          Theme, backend connectivity, and about this app.
        </p>
      </div>

      <SettingsView />
    </div>
  );
}
