import { FileText, Folder, Layers, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Workspace } from "@/lib/types";

interface LeftSidebarProps {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
  onCreate: () => void;
}

/** Left rail: workspaces, plus per-workspace subjects and documents (later phases). */
export function LeftSidebar({
  workspaces,
  activeWorkspaceId,
  loading,
  onSelect,
  onCreate,
}: LeftSidebarProps) {
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-card/40">
      <div className="flex items-center justify-between px-3 pb-1 pt-3">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Workspaces
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={onCreate}
          aria-label="New workspace"
        >
          <Plus className="size-3.5" />
        </Button>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-1">
        {loading ? (
          <SidebarSkeleton />
        ) : workspaces.length === 0 ? (
          <p className="px-2 py-6 text-center text-xs text-muted-foreground">
            No workspaces yet. Create one to start.
          </p>
        ) : (
          workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => onSelect(ws.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm",
                ws.id === activeWorkspaceId
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
              )}
            >
              <Folder className="size-3.5 shrink-0" />
              <span className="truncate">{ws.name}</span>
            </button>
          ))
        )}
      </nav>

      <div className="border-t border-border px-2 py-2">
        <SidebarLink icon={<Layers className="size-3.5" />} label="Subjects" />
        <SidebarLink icon={<FileText className="size-3.5" />} label="Documents" />
      </div>
    </aside>
  );
}

function SidebarLink({
  icon,
  label,
}: {
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <div className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground">
      {icon}
      <span>{label}</span>
    </div>
  );
}

function SidebarSkeleton() {
  return (
    <div className="space-y-1.5 px-1 py-2">
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-7 animate-pulse rounded-md bg-secondary/60" />
      ))}
    </div>
  );
}
