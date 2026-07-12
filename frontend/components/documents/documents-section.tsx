"use client";

import * as React from "react";
import { FileText, Loader2, Plus, Trash2 } from "lucide-react";

import { UploadDropzone } from "@/components/documents/upload-dropzone";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { DocumentItem } from "@/lib/types";

/** Left-sidebar documents list for the active workspace, with upload + live status. */
export function DocumentsSection({ workspaceId }: { workspaceId: string | null }) {
  const [docs, setDocs] = React.useState<DocumentItem[]>([]);
  const [uploadOpen, setUploadOpen] = React.useState(false);

  const refresh = React.useCallback(async () => {
    if (!workspaceId) {
      setDocs([]);
      return;
    }
    try {
      setDocs(await api.documents.list(workspaceId));
    } catch {
      /* keep previous list on transient errors */
    }
  }, [workspaceId]);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while anything is still processing.
  const processing = docs.some(
    (d) => d.status === "queued" || d.status === "processing",
  );
  React.useEffect(() => {
    if (!processing) return;
    const t = setInterval(refresh, 2500);
    return () => clearInterval(t);
  }, [processing, refresh]);

  const handleDelete = async (id: string) => {
    await api.documents.remove(id);
    setDocs((prev) => prev.filter((d) => d.id !== id));
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center justify-between px-1 py-1">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Documents
        </span>
        <button
          onClick={() => setUploadOpen(true)}
          disabled={!workspaceId}
          className="flex h-5 w-5 items-center justify-center rounded text-muted-foreground hover:bg-secondary disabled:opacity-40"
          aria-label="Upload documents"
        >
          <Plus className="size-3.5" />
        </button>
      </div>

      <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto">
        {docs.length === 0 ? (
          <p className="px-1 py-2 text-xs text-muted-foreground/70">
            {workspaceId ? "No documents yet." : "Select a workspace."}
          </p>
        ) : (
          docs.map((doc) => (
            <div
              key={doc.id}
              className="group flex items-center gap-2 rounded-md px-1.5 py-1 text-sm text-muted-foreground hover:bg-secondary/60"
              title={doc.error ?? doc.filename}
            >
              <StatusDot status={doc.status} />
              <FileText className="size-3.5 shrink-0 opacity-60" />
              <span className="flex-1 truncate text-foreground/90">
                {doc.title || doc.filename}
              </span>
              {doc.status === "ready" && (
                <span className="text-[10px] text-muted-foreground">
                  {doc.chunk_count}
                </span>
              )}
              <button
                onClick={() => handleDelete(doc.id)}
                className="hidden text-muted-foreground hover:text-destructive group-hover:block"
                aria-label="Delete document"
              >
                <Trash2 className="size-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      {workspaceId && (
        <UploadDropzone
          open={uploadOpen}
          workspaceId={workspaceId}
          onClose={() => setUploadOpen(false)}
          onUploaded={refresh}
        />
      )}
    </div>
  );
}

function StatusDot({ status }: { status: DocumentItem["status"] }) {
  if (status === "processing" || status === "queued") {
    return <Loader2 className="size-3 shrink-0 animate-spin text-amber-500" />;
  }
  return (
    <span
      className={cn(
        "size-1.5 shrink-0 rounded-full",
        status === "ready" ? "bg-emerald-500" : "bg-destructive",
      )}
    />
  );
}
