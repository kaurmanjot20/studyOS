"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";

import { Markdown } from "@/components/chat/markdown";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";

export function ResumeView({ workspaceId }: { workspaceId: string }) {
  const [docs, setDocs] = React.useState<DocumentItem[]>([]);
  const [docId, setDocId] = React.useState("");
  const [loading, setLoading] = React.useState<"review" | "questions" | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [review, setReview] = React.useState("");
  const [questions, setQuestions] = React.useState<string[]>([]);

  React.useEffect(() => {
    api.documents
      .list(workspaceId)
      .then((all) => {
        const ready = all.filter((d) => d.status === "ready");
        setDocs(ready);
        setDocId((cur) => cur || ready[0]?.id || "");
      })
      .catch(() => setDocs([]));
  }, [workspaceId]);

  const run = async (kind: "review" | "questions") => {
    if (!docId) return;
    setLoading(kind);
    setError(null);
    try {
      if (kind === "review") {
        setReview((await api.resume.review(workspaceId, docId)).markdown);
      } else {
        setQuestions((await api.resume.questions(workspaceId, docId)).questions);
      }
    } catch {
      setError("Couldn't process the resume. Check your AI provider in Settings.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <h2 className="text-base font-medium">Resume review</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Upload your resume in the Documents panel, then review it or generate
        resume-specific interview questions.
      </p>

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
