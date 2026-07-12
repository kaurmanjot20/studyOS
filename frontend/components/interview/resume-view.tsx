"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";

import { Markdown } from "@/components/chat/markdown";
import { Button } from "@/components/ui/button";
import { HistoryMenu } from "@/components/ui/history-menu";
import { api } from "@/lib/api";
import type { ArtifactSummary, DocumentItem } from "@/lib/types";

export function ResumeView({ workspaceId }: { workspaceId: string }) {
  const [docs, setDocs] = React.useState<DocumentItem[]>([]);
  const [docId, setDocId] = React.useState("");
  const [loading, setLoading] = React.useState<"review" | "questions" | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [review, setReview] = React.useState("");
  const [questions, setQuestions] = React.useState<string[]>([]);
  const [history, setHistory] = React.useState<ArtifactSummary[]>([]);
  const [activeId, setActiveId] = React.useState<string | null>(null);

  const loadHistory = React.useCallback(async () => {
    try {
      const [rev, qs] = await Promise.all([
        api.study.history(workspaceId, "resume_review"),
        api.study.history(workspaceId, "resume_questions"),
      ]);
      setHistory(
        [...rev, ...qs].sort((a, b) => b.created_at.localeCompare(a.created_at)),
      );
    } catch {
      setHistory([]);
    }
  }, [workspaceId]);

  React.useEffect(() => {
    loadHistory();
    api.documents
      .list(workspaceId)
      .then((all) => {
        const ready = all.filter((d) => d.status === "ready");
        setDocs(ready);
        setDocId((cur) => cur || ready[0]?.id || "");
      })
      .catch(() => setDocs([]));
  }, [workspaceId, loadHistory]);

  const run = async (kind: "review" | "questions") => {
    if (!docId) return;
    setLoading(kind);
    setError(null);
    try {
      if (kind === "review") {
        const a = await api.resume.review(workspaceId, docId);
        setReview((a.payload.markdown as string) ?? "");
        setQuestions([]);
        setActiveId(a.id);
      } else {
        const a = await api.resume.questions(workspaceId, docId);
        setQuestions((a.payload.questions as string[]) ?? []);
        setReview("");
        setActiveId(a.id);
      }
      loadHistory();
    } catch {
      setError("Couldn't process the resume. Check your AI provider in Settings.");
    } finally {
      setLoading(null);
    }
  };

  const openArtifact = async (id: string) => {
    try {
      const a = await api.study.artifact(id);
      if (a.kind === "resume_review") {
        setReview((a.payload.markdown as string) ?? "");
        setQuestions([]);
      } else {
        setQuestions((a.payload.questions as string[]) ?? []);
        setReview("");
      }
      setActiveId(id);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-base font-medium">Resume review</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload your resume in the Documents panel, then review it or generate
            resume-specific interview questions.
          </p>
        </div>
        <HistoryMenu
          items={history.map((h) => ({
            id: h.id,
            title: h.title,
            subtitle: `${h.kind === "resume_review" ? "Review" : "Questions"} · ${new Date(h.created_at).toLocaleDateString()}`,
          }))}
          activeId={activeId}
          onOpen={openArtifact}
          onRename={async (id, title) => {
            await api.study.renameArtifact(id, title);
            loadHistory();
          }}
          onDelete={async (id) => {
            await api.study.deleteArtifact(id);
            loadHistory();
          }}
        />
      </div>

      {docs.length === 0 ? (
        <p className="mt-6 rounded-md border border-border bg-card px-3 py-4 text-sm text-muted-foreground">
          No processed documents yet. Upload your resume (PDF/DOCX) via the{" "}
          <span className="text-foreground">+</span> in the Documents panel.
        </p>
      ) : (
        <>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <select
              value={docId}
              onChange={(e) => setDocId(e.target.value)}
              className="h-9 min-w-[200px] flex-1 rounded-md border border-input bg-transparent px-2 text-sm"
            >
              {docs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title || d.filename}
                </option>
              ))}
            </select>
            <Button variant="outline" onClick={() => run("review")} disabled={loading !== null}>
              {loading === "review" ? <Loader2 className="size-4 animate-spin" /> : "Review resume"}
            </Button>
            <Button variant="accent" onClick={() => run("questions")} disabled={loading !== null}>
              {loading === "questions" ? <Loader2 className="size-4 animate-spin" /> : "Generate questions"}
            </Button>
          </div>

          {error && <p className="mt-3 text-xs text-destructive">{error}</p>}

          {review && (
            <div className="mt-5 rounded-lg border border-border bg-card/50 p-5">
              <Markdown>{review}</Markdown>
            </div>
          )}

          {questions.length > 0 && (
            <div className="mt-5 rounded-lg border border-border bg-card/50 p-4">
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Resume-specific questions
              </div>
              <ol className="list-decimal space-y-2 pl-5 text-sm">
                {questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ol>
            </div>
          )}
        </>
      )}
    </div>
  );
}
