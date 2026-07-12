"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";

import { Markdown } from "@/components/chat/markdown";
import { StudyConfigBar } from "@/components/study/study-config-bar";
import { api } from "@/lib/api";

export function RevisionView({ workspaceId }: { workspaceId: string }) {
  const [subject, setSubject] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [markdown, setMarkdown] = React.useState("");

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.study.revision(workspaceId, { subject });
      setMarkdown(res.markdown);
    } catch {
      setError("Couldn't generate revision notes. Check your AI provider in Settings.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
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
