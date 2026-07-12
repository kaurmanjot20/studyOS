"use client";

import * as React from "react";
import { Check, History, Pencil, Trash2, X } from "lucide-react";

import { cn } from "@/lib/utils";

export interface HistoryMenuItem {
  id: string;
  title: string;
  subtitle?: string;
}

interface HistoryMenuProps {
  items: HistoryMenuItem[];
  activeId?: string | null;
  onOpen: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
  label?: string;
}

/** A themed history dropdown: each row opens an item, with inline rename + delete.
 * Replaces native <select> so it's readable in dark mode and can hold per-item actions. */
export function HistoryMenu({
  items,
  activeId,
  onOpen,
  onRename,
  onDelete,
  label = "History",
}: HistoryMenuProps) {
  const [open, setOpen] = React.useState(false);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [draft, setDraft] = React.useState("");
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setEditingId(null);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  const startEdit = (item: HistoryMenuItem) => {
    setEditingId(item.id);
    setDraft(item.title);
  };

  const commit = (id: string) => {
    const t = draft.trim();
    if (t) onRename(id, t);
    setEditingId(null);
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex h-8 items-center gap-1.5 rounded-md border border-border bg-card px-2.5 text-xs text-muted-foreground hover:bg-secondary"
      >
        <History className="size-3.5" />
        {label}
        <span className="rounded bg-secondary px-1 text-[10px]">{items.length}</span>
      </button>

      {open && (
        <div className="absolute right-0 z-40 mt-1 w-80 overflow-hidden rounded-lg border border-border bg-popover shadow-xl">
          <div className="max-h-80 overflow-y-auto p-1">
            {items.length === 0 ? (
              <p className="px-3 py-6 text-center text-xs text-muted-foreground">
                Nothing saved yet.
              </p>
            ) : (
              items.map((item) => (
                <div
                  key={item.id}
                  className={cn(
                    "group flex items-center gap-1 rounded-md px-1.5 py-1",
                    item.id === activeId ? "bg-secondary" : "hover:bg-secondary/60",
                  )}
                >
                  {editingId === item.id ? (
                    <>
                      <input
                        autoFocus
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") commit(item.id);
                          if (e.key === "Escape") setEditingId(null);
                        }}
                        className="h-7 flex-1 rounded border border-input bg-background px-2 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      />
                      <IconBtn onClick={() => commit(item.id)} title="Save">
                        <Check className="size-3.5 text-emerald-500" />
                      </IconBtn>
                      <IconBtn onClick={() => setEditingId(null)} title="Cancel">
                        <X className="size-3.5" />
                      </IconBtn>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          onOpen(item.id);
                          setOpen(false);
                        }}
                        className="min-w-0 flex-1 text-left"
                      >
                        <div className="truncate text-xs text-foreground/90">
                          {item.title}
                        </div>
                        {item.subtitle && (
                          <div className="truncate text-[10px] text-muted-foreground">
                            {item.subtitle}
                          </div>
                        )}
                      </button>
                      <div className="hidden shrink-0 items-center gap-0.5 group-hover:flex">
                        <IconBtn onClick={() => startEdit(item)} title="Rename">
                          <Pencil className="size-3.5" />
                        </IconBtn>
                        <IconBtn onClick={() => onDelete(item.id)} title="Delete">
                          <Trash2 className="size-3.5 hover:text-destructive" />
                        </IconBtn>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function IconBtn({
  onClick,
  title,
  children,
}: {
  onClick: () => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="flex size-6 items-center justify-center rounded text-muted-foreground hover:bg-background"
    >
      {children}
    </button>
  );
}
