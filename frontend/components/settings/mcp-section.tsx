"use client";

import * as React from "react";
import { Loader2, Plug } from "lucide-react";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { McpServerStatus } from "@/lib/types";

/** MCP servers status inside Settings. Connecting spawns the servers, so this loads
 * lazily and shows a spinner while it probes. */
export function McpSection({ open }: { open: boolean }) {
  const [servers, setServers] = React.useState<McpServerStatus[] | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (!open) return;
    setLoading(true);
    api.mcp
      .servers()
      .then(setServers)
      .catch(() => setServers([]))
      .finally(() => setLoading(false));
  }, [open]);

  return (
    <div className="border-t border-border pt-4">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        <Plug className="size-3.5" /> MCP Integrations
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="size-3.5 animate-spin" /> Probing servers…
        </div>
      )}

      {servers && (
        <ul className="space-y-1.5">
          {servers.map((s) => (
            <li
              key={s.name}
              className="flex items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1.5 text-sm"
            >
              <span
                className={cn(
                  "size-1.5 shrink-0 rounded-full",
                  s.connected
                    ? "bg-emerald-500"
                    : s.enabled
                      ? "bg-destructive"
                      : "bg-muted-foreground/40",
                )}
              />
              <span className="font-medium">{s.label}</span>
              <span className="ml-auto text-xs text-muted-foreground">
                {s.connected
                  ? `${s.tools.length} tools`
                  : s.requires
                    ? `needs ${s.requires}`
                    : s.enabled
                      ? "unavailable"
                      : "disabled"}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-1.5 text-[11px] text-muted-foreground/70">
        Configure servers in the backend env (filesystem enabled by default; Notion needs
        an integration token).
      </p>
    </div>
  );
}
