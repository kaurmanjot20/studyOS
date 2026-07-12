"use client";

import * as React from "react";
import { FileText, Folder, MessageSquare, Search } from "lucide-react";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { WorkspaceMode } from "@/components/shell/center";

interface Flat {
  type: "workspace" | "document" | "chat";
  id: string;
  label: string;
  workspaceId: string;
}

interface GlobalSearchProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (target: { workspaceId: string; mode?: WorkspaceMode }) => void;
}

const ICON = {
  workspace: Folder,
  document: FileText,
  chat: MessageSquare,
} as const;

const GROUP_LABEL = {
  workspace: "Workspace",
  document: "Document",
  chat: "Chat",
} as const;

/** Global ⌘/Ctrl+K search across workspaces, documents, and chats. */
export function GlobalSearch({ open, onClose, onNavigate }: GlobalSearchProps) {
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<Flat[]>([]);
  const [active, setActive] = React.useState(0);

  React.useEffect(() => {
    if (open) {
      setQuery("");
      setResults([]);
      setActive(0);
    }
  }, [open]);

  // Debounced search.
  React.useEffect(() => {
    if (!open) return;
    const q = query.trim();
    if (!q) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const r = await api.search(q);
        const flat: Flat[] = [
          ...r.workspaces.map((w) => ({
            type: "workspace" as const,
            id: w.id,
            label: w.label,
            workspaceId: w.id,
          })),
          ...r.documents.map((d) => ({
            type: "document" as const,
            id: d.id,
            label: d.label,
            workspaceId: d.workspace_id ?? "",
          })),
          ...r.chats.map((c) => ({
            type: "chat" as const,
            id: c.id,
            label: c.label,
            workspaceId: c.workspace_id ?? "",
          })),
        ];
        setResults(flat);
        setActive(0);
      } catch {
        setResults([]);
      }
    }, 180);
    return () => clearTimeout(t);
  }, [query, open]);

  const choose = (hit: Flat) => {
    if (!hit.workspaceId) return;
    onNavigate({
      workspaceId: hit.workspaceId,
      mode: hit.type === "chat" ? "chat" : undefined,
    });
    onClose();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") onClose();
    else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter" && results[active]) {
      choose(results[active]);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-[15vh]"
      onMouseDown={onClose}
    >
      <div
        className="w-full max-w-xl overflow-hidden rounded-xl border border-border bg-popover shadow-2xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2.5 border-b border-border px-3.5">
          <Search className="size-4 text-muted-foreground" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search workspaces, documents, chats…"
            className="h-12 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
        </div>

        <div className="max-h-[50vh] overflow-y-auto p-1.5">
          {query.trim() && results.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              No results for “{query.trim()}”.
            </p>
          ) : !query.trim() ? (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              Type to search across all your workspaces.
            </p>
          ) : (
            results.map((hit, i) => {
              const Icon = ICON[hit.type];
              return (
                <button
                  key={`${hit.type}-${hit.id}`}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => choose(hit)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm",
                    i === active ? "bg-secondary" : "hover:bg-secondary/60",
                  )}
                >
                  <Icon className="size-4 shrink-0 text-muted-foreground" />
                  <span className="flex-1 truncate">{hit.label}</span>
                  <span className="shrink-0 rounded bg-background px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                    {GROUP_LABEL[hit.type]}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
