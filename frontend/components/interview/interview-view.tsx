"use client";

import * as React from "react";
import { Loader2, Send } from "lucide-react";

import { Markdown } from "@/components/chat/markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { InterviewSession } from "@/lib/types";

export function InterviewView({ workspaceId }: { workspaceId: string }) {
  const [company, setCompany] = React.useState("");
  const [subject, setSubject] = React.useState("");
  const [difficulty, setDifficulty] = React.useState("medium");
  const [count, setCount] = React.useState(5);
  const [session, setSession] = React.useState<InterviewSession | null>(null);
  const [answer, setAnswer] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const start = async () => {
    setBusy(true);
    setError(null);
    try {
      setSession(
        await api.interview.start(workspaceId, {
          company,
          subject,
          difficulty,
          target_questions: count,
        }),
      );
    } catch {
      setError("Couldn't start the interview. Check your AI provider in Settings.");
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    if (!session || !answer.trim()) return;
    setBusy(true);
    try {
      const updated = await api.interview.answer(session.id, answer.trim());
      setSession(updated);
      setAnswer("");
    } catch {
      setError("Couldn't submit your answer.");
    } finally {
      setBusy(false);
    }
  };

  if (!session) {
    return (
      <div className="mx-auto max-w-md px-4 py-10">
        <h2 className="text-base font-medium">Mock interview</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          The interviewer asks questions, evaluates your answers, and tracks weak areas.
        </p>
        <div className="mt-5 space-y-3">
          <Field label="Company (optional)">
            <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Google" />
          </Field>
          <Field label="Subject">
            <Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Operating Systems" />
          </Field>
          <div className="flex gap-3">
            <Field label="Difficulty">
              <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="h-9 w-full rounded-md border border-input bg-transparent px-2 text-sm">
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </Field>
            <Field label="Questions">
              <select value={count} onChange={(e) => setCount(Number(e.target.value))} className="h-9 w-full rounded-md border border-input bg-transparent px-2 text-sm">
                {[3, 5, 8].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </Field>
          </div>
          {error && <p className="text-xs text-destructive">{error}</p>}
          <Button variant="accent" className="w-full" onClick={start} disabled={busy}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : "Start interview"}
          </Button>
        </div>
      </div>
    );
  }

  const answered = session.transcript.filter((t) => t.answer !== undefined);
  const current =
    session.status === "active" ? session.transcript[session.transcript.length - 1] : null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {session.company ? `${session.company} · ` : ""}
          {session.subject} · {session.difficulty}
        </div>
        <div className="text-xs text-muted-foreground">
          {session.asked_count}/{session.target_questions}
        </div>
      </div>

      <div className="space-y-4">
        {answered.map((t, i) => (
          <div key={i} className="rounded-lg border border-border bg-card/50 p-4">
            <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
              {t.topic}
            </div>
            <div className="mt-1 text-sm font-medium">Q{i + 1}. {t.question}</div>
            <div className="mt-2 rounded-md bg-secondary px-3 py-2 text-sm">{t.answer}</div>
            {t.score !== undefined && (
              <div className="mt-2 flex items-start gap-2">
                <ScoreBadge score={t.score} />
                <p className="text-xs text-muted-foreground">{t.feedback}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {current && (
        <div className="mt-4 rounded-lg border border-accent/30 bg-card p-4">
          <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
            {current.topic}
          </div>
          <div className="mt-1 text-sm font-medium">
            Q{session.asked_count}. {current.question}
          </div>
          <div className="mt-3 flex items-end gap-2">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={3}
              placeholder="Your answer…"
              className="flex-1 resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <Button variant="accent" size="icon" onClick={submit} disabled={busy || !answer.trim()}>
              {busy ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            </Button>
          </div>
        </div>
      )}

      {session.status === "completed" && (
        <div className="mt-4 rounded-lg border border-border bg-card p-5">
          <div className="mb-2 text-lg font-semibold">
            Result: <span className={scoreColor(session.score ?? 0)}>{session.score}%</span>
          </div>
          {session.summary && <Markdown>{session.summary}</Markdown>}
          <Button variant="outline" className="mt-4" onClick={() => setSession(null)}>
            New interview
          </Button>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex-1 space-y-1.5">
      <label className="text-xs text-muted-foreground">{label}</label>
      {children}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium",
        score >= 7
          ? "bg-emerald-500/15 text-emerald-400"
          : score >= 4
            ? "bg-amber-500/15 text-amber-400"
            : "bg-destructive/15 text-destructive",
      )}
    >
      {score}/10
    </span>
  );
}

function scoreColor(pct: number) {
  return pct >= 70 ? "text-emerald-400" : pct >= 40 ? "text-amber-400" : "text-destructive";
}
