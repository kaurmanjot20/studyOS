import { ChevronDown, Search, Settings, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Workspace } from "@/lib/types";

interface TopNavProps {
  activeWorkspace: Workspace | null;
  activeProviderLabel: string | null;
  onOpenWorkspaces: () => void;
  onOpenSettings: () => void;
  onOpenSearch: () => void;
}

/** Top bar: workspace selector, global search, provider status, settings. */
export function TopNav({
  activeWorkspace,
  activeProviderLabel,
  onOpenWorkspaces,
  onOpenSettings,
  onOpenSearch,
}: TopNavProps) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-border px-3">
      <div className="flex items-center gap-2 pr-1">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-accent text-accent-foreground">
          <Sparkles className="size-3.5" />
        </div>
        <span className="font-display text-[15px] font-semibold tracking-tight">
          StudyOS
        </span>
      </div>

      <div className="h-4 w-px bg-border" />

      <button
        onClick={onOpenWorkspaces}
        className="flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-foreground/90 hover:bg-secondary"
      >
        {activeWorkspace ? activeWorkspace.name : "Select workspace"}
        <ChevronDown className="size-3.5 text-muted-foreground" />
      </button>

      <div className="mx-auto flex w-full max-w-md items-center">
        <button
          onClick={onOpenSearch}
          className="flex w-full items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:border-muted-foreground/40 hover:text-foreground"
        >
          <Search className="size-3.5" />
          <span className="flex-1 text-left">Search everything…</span>
        </button>
      </div>

      <div className="ml-auto flex items-center gap-1">
        <button
          onClick={onOpenSettings}
          className="flex items-center gap-1.5 rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground hover:bg-secondary"
        >
          <span
            className={
              activeProviderLabel
                ? "size-1.5 rounded-full bg-emerald-500"
                : "size-1.5 rounded-full bg-muted-foreground/50"
            }
          />
          {activeProviderLabel ?? "No provider"}
        </button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Settings"
          onClick={onOpenSettings}
        >
          <Settings className="size-4" />
        </Button>
      </div>
    </header>
  );
}
