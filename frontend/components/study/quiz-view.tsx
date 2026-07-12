"use client";

import * as React from "react";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";

import { StudyConfigBar } from "@/components/study/study-config-bar";
import { Button } from "@/components/ui/button";
import { HistoryMenu } from "@/components/ui/history-menu";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ArtifactSummary, QuizQuestion, QuizScoreResult } from "@/lib/types";

export function QuizView({ workspaceId }: { workspaceId: string }) {
  const [subject, setSubject] = React.useState("");
  const [difficulty, setDifficulty] = React.useState("medium");
  const [count, setCount] = React.useState(5);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [questions, setQuestions] = React.useState<QuizQuestion[]>([]);
  const [answers, setAnswers] = React.useState<(number | null)[]>([]);
  const [result, setResult] = React.useState<QuizScoreResult | null>(null);
  const [history, setHistory] = React.useState<ArtifactSummary[]>([]);
  const [activeId, setActiveId] = React.useState<string | null>(null);

  const loadHistory = React.useCallback(async () => {
    try {
      setHistory(await api.study.history(workspaceId, "quiz"));
    } catch {
      setHistory([]);
    }
  }, [workspaceId]);

  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const showQuestions = (qs: QuizQuestion[], id: string | null) => {
    setQuestions(qs);
    setAnswers(new Array(qs.length).fill(null));
    setActiveId(id);
    setResult(null);
  };

  const generate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.study.quiz(workspaceId, { subject, difficulty, count });
      showQuestions((res.payload.questions as QuizQuestion[]) ?? [], res.id);
      loadHistory();
    } catch {
      setError("Couldn't generate the quiz. Check your AI provider in Settings.");
    } finally {
      setLoading(false);
    }
  };

  const openArtifact = async (id: string) => {
    try {
      const a = await api.study.artifact(id);
      showQuestions((a.payload.questions as QuizQuestion[]) ?? [], id);
    } catch {
      /* ignore */
    }
  };

  const submit = async () => {
    const items = questions.map((q, i) => ({
      topic: q.topic,
      answer_index: q.answer_index,
      selected_index: answers[i],
    }));
    try {
      setResult(await api.study.scoreQuiz(workspaceId, items));
    } catch {
      setError("Couldn't score the quiz.");
    }
  };

  const allAnswered = answers.length > 0 && answers.every((a) => a !== null);

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
            if (activeId === id) showQuestions([], null);
            loadHistory();
          }}
        />
      </div>
      <StudyConfigBar
        subject={subject}
        onSubject={setSubject}
        onGenerate={generate}
        loading={loading}
        cta="Generate quiz"
        extra={
          <>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="h-9 rounded-md border border-input bg-transparent px-2 text-sm"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            <select
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="h-9 rounded-md border border-input bg-transparent px-2 text-sm"
            >
              {[3, 5, 8, 10].map((n) => (
                <option key={n} value={n}>
                  {n} Qs
                </option>
              ))}
            </select>
          </>
        }
      />

      {error && (
        <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-4 rounded-lg border border-border bg-card p-4">
          <div className="text-lg font-semibold">
            {result.correct}/{result.total}{" "}
            <span className="text-muted-foreground">({result.score_pct}%)</span>
          </div>
          {result.weak_topics_recorded.length > 0 && (
            <p className="mt-1 text-xs text-muted-foreground">
              Added to your weak topics: {result.weak_topics_recorded.join(", ")}.
              Revision will prioritize these.
            </p>
          )}
        </div>
      )}

      <div className="mt-5 space-y-5">
        {questions.map((q, qi) => (
          <div key={qi} className="rounded-lg border border-border bg-card/50 p-4">
            <div className="mb-2 text-[11px] uppercase tracking-wide text-muted-foreground">
              {q.topic}
            </div>
            <div className="mb-3 text-sm font-medium">
              {qi + 1}. {q.question}
            </div>
            <div className="space-y-1.5">
              {q.options.map((opt, oi) => {
                const chosen = answers[qi] === oi;
                const isCorrect = oi === q.answer_index;
                const graded = result !== null;
                return (
                  <button
                    key={oi}
                    disabled={graded}
                    onClick={() =>
                      setAnswers((prev) => {
                        const next = [...prev];
                        next[qi] = oi;
                        return next;
                      })
                    }
                    className={cn(
                      "flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                      graded && isCorrect && "border-emerald-500/40 bg-emerald-500/10",
                      graded && chosen && !isCorrect && "border-destructive/40 bg-destructive/10",
                      !graded && chosen && "border-accent bg-accent/5",
                      !graded && !chosen && "border-border hover:border-muted-foreground/40",
                      graded && !isCorrect && !chosen && "border-border opacity-70",
                    )}
                  >
                    {graded && isCorrect && (
                      <CheckCircle2 className="size-4 shrink-0 text-emerald-500" />
                    )}
                    {graded && chosen && !isCorrect && (
                      <XCircle className="size-4 shrink-0 text-destructive" />
                    )}
                    <span>{opt}</span>
                  </button>
                );
              })}
            </div>
            {result && q.explanation && (
              <p className="mt-2 text-xs text-muted-foreground">{q.explanation}</p>
            )}
          </div>
        ))}
      </div>

      {questions.length > 0 && !result && (
        <div className="mt-5 flex justify-end">
          <Button variant="accent" onClick={submit} disabled={!allAnswered}>
            Submit answers
          </Button>
        </div>
      )}

      {questions.length === 0 && !loading && (
        <EmptyHint text="Generate a quiz from your notes (or general knowledge). Wrong answers become weak topics your revision will prioritize." />
      )}
      {loading && <Loading />}
    </div>
  );
}

function EmptyHint({ text }: { text: string }) {
  return (
    <p className="mt-10 text-center text-sm text-muted-foreground">{text}</p>
  );
}

function Loading() {
  return (
    <div className="mt-10 flex justify-center">
      <Loader2 className="size-5 animate-spin text-muted-foreground" />
    </div>
  );
}
