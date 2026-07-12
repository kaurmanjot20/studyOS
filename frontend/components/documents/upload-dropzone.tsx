"use client";

import * as React from "react";
import { FileUp, Loader2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const ACCEPT = ".pdf,.docx,.pptx,.txt,.md,.png,.jpg,.jpeg";

interface UploadDropzoneProps {
  open: boolean;
  workspaceId: string;
  onClose: () => void;
  onUploaded: () => void;
}

interface Upload {
  file: File;
  percent: number;
  error?: string;
  done?: boolean;
}

export function UploadDropzone({
  open,
  workspaceId,
  onClose,
  onUploaded,
}: UploadDropzoneProps) {
  const [uploads, setUploads] = React.useState<Upload[]>([]);
  const [dragging, setDragging] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (open) setUploads([]);
  }, [open]);

  if (!open) return null;

  const patch = (i: number, p: Partial<Upload>) =>
    setUploads((prev) => prev.map((u, idx) => (idx === i ? { ...u, ...p } : u)));

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const list = Array.from(files);
    const base = uploads.length;
    setUploads((prev) => [...prev, ...list.map((file) => ({ file, percent: 0 }))]);

    for (let i = 0; i < list.length; i++) {
      const idx = base + i;
      try {
        await api.documents.upload(workspaceId, list[i], (p) =>
          patch(idx, { percent: p }),
        );
        patch(idx, { percent: 100, done: true });
        onUploaded();
      } catch (err) {
        patch(idx, {
          error: err instanceof Error ? err.message : "Upload failed",
        });
      }
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg border border-border bg-popover p-4 shadow-xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Upload documents</h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={cn(
            "flex w-full flex-col items-center gap-2 rounded-lg border border-dashed px-4 py-8 text-center transition-colors",
            dragging
              ? "border-accent bg-accent/5"
              : "border-border hover:border-muted-foreground/40",
          )}
        >
          <FileUp className="size-5 text-muted-foreground" />
          <span className="text-sm">
            Drop files here, or <span className="text-accent">browse</span>
          </span>
          <span className="text-xs text-muted-foreground">
            PDF, DOCX, PPTX, TXT, images
          </span>
        </button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {uploads.length > 0 && (
          <ul className="mt-3 space-y-2">
            {uploads.map((u, i) => (
              <li key={i} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="truncate">{u.file.name}</span>
                  <span className="text-muted-foreground">
                    {u.error ? (
                      <span className="text-destructive">{u.error}</span>
                    ) : u.done ? (
                      "processing…"
                    ) : (
                      `${u.percent}%`
                    )}
                  </span>
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-secondary">
                  <div
                    className={cn(
                      "h-full transition-all",
                      u.error ? "bg-destructive" : "bg-accent",
                    )}
                    style={{ width: `${u.error ? 100 : u.percent}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}

        <div className="mt-4 flex justify-end">
          <Button variant="outline" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
}
