"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight, Loader2, RotateCw } from "lucide-react";

import { StudyConfigBar } from "@/components/study/study-config-bar";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Flashcard } from "@/lib/types";

export function FlashcardsView({ workspaceId }: { workspaceId: string }) {
  const [subject, setSubject] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [cards, setCards] = React.useState<Flashcard[]>([]);
  const [index, setIndex] = React.useState(0);
  const [flipped, setFlipped] = React.useState(false);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.study.flashcards(workspaceId, { subject, count: 8 });
      setCards(res.cards);
      setIndex(0);
      setFlipped(false);
    } catch {
      setError("Couldn't generate flashcards. Check your AI provider in Settings.");
    } finally {
      setLoading(false);
    }
  };

  const go = (delta: number) => {
    setFlipped(false);
    setIndex((i) => (i + delta + cards.length) % cards.length);
  };

  const card = cards[index];

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <StudyConfigBar
        subject={subject}
        onSubject={setSubject}
        onGenerate={generate}
        loading={loading}
        cta="Generate cards"
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

      {card && (
        <div className="mt-6">
          <button
            onClick={() => setFlipped((f) => !f)}
            className="flex min-h-[220px] w-full flex-col items-center justify-center gap-3 rounded-xl border border-border bg-card p-6 text-center transition-colors hover:border-muted-foreground/40"
          >
            <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
              {flipped ? "Answer" : "Question"}
            </span>
            <span className="text-base leading-relaxed">
              {flipped ? card.back : card.front}
            </span>
            <span className="mt-2 inline-flex items-center gap-1 text-xs text-muted-foreground">
              <RotateCw className="size-3" /> click to flip
            </span>
          </button>

          <div className="mt-4 flex items-center justify-between">
            <Button variant="outline" size="sm" onClick={() => go(-1)}>
              <ChevronLeft className="size-4" /> Prev
            </Button>
            <span className="text-xs text-muted-foreground">
              {index + 1} / {cards.length}
            </span>
            <Button variant="outline" size="sm" onClick={() => go(1)}>
              Next <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}

      {cards.length === 0 && !loading && (
        <p className="mt-10 text-center text-sm text-muted-foreground">
          Generate spaced-repetition flashcards from your notes or a topic.
        </p>
      )}
    </div>
  );
}
