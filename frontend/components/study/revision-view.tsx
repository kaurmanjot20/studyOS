"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";

import { Markdown } from "@/components/chat/markdown";
import { StudyConfigBar } from "@/components/study/study-config-bar";
import { HistoryMenu } from "@/components/ui/history-menu";
import { api } from "@/lib/api";
import type { ArtifactSummary } from "@/lib/types";

export function RevisionView({ workspaceId }: { workspaceId: string }) {
  const [subject, setSubject] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [markdown, setMarkdown] = React.useState("");
  const [history, setHistory] = React.useState<ArtifactSummary[]>([]);
  const [activeId, setActiveId] = React.useState<string | null>(null);

  const loadHistory = React.useCallback(async () => {
    try {
      setHistory(await api.study.history(workspaceId, "revision"));
    } catch {
      setHistory([]);
    }
  }, [workspaceId]);

  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.study.revision(workspaceId, { subject });
      setMarkdown((res.payload.markdown as string) ?? "");
      setActiveId(res.id);
      loadHistory();
    } catch {
      setError("Couldn't generate revision notes. Check your AI provider in Settings.");
    } finally {
      setLoading(false);
    }
  };

  const openArtifact = async (id: string) => {
    try {
      const a = await api.study.artifact(id);
      setMarkdown((a.payload.markdown as string) ?? "");
      setActiveId(id);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <div className="mb-2 flex justify-end">
        <HistoryMenu
          items={history.map((h) => ({
            id: h.id,
            title: h.title,
            subtitle: new Date(h.created_at).toLocaleString(),
          }))}
          activeId={activeId}
          onOpen={openArtifact}
          onRename={async (id, title) => {
            await api.study.renameArtifact(id, title);
            loadHistory();
          }}
          onDelete={async (id) => {
            await api.study.deleteArtifact(id);
            if (activeId === id) {
              setMarkdown("");
              setActiveId(null);
            }
            loadHistory();
          }}
        />
      </div>
      <StudyConfigBar
        subject={subject}
        onSubject={setSubject}
        onGenerate={generate}
        loading={loading}
        cta="Generate notes"
      />

      {error && (
        <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {error}
        </p>
      )}

      {loading && (
        <div className="mt-10 flex justify-center">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </div>
      )}

      {markdown ? (
        <div className="mt-6 rounded-lg border border-border bg-card/50 p-5">
          <Markdown>{markdown}</Markdown>
        </div>
      ) : (
        !loading && (
          <p className="mt-10 text-center text-sm text-muted-foreground">
            Generate a one-page revision cheat sheet from your notes or a topic.
          </p>
        )
      )}
    </div>
  );
}
