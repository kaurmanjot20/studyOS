"use client";

import * as React from "react";
import { BookOpen, Brain, Sparkles, TriangleAlert, UploadCloud } from "lucide-react";

import { type Trace } from "@/components/chat/chat-view";
import { api } from "@/lib/api";
import type { MemoryItem } from "@/lib/types";

/** Right rail: planner trace + retrieved sources for the current turn, plus the learner's
 * memory (weak topics + preferences) that the planner consults before answering. */
export function RightSidebar({
  trace,
  workspaceId,
}: {
  trace: Trace;
  workspaceId: string | null;
}) {
  const plan = trace.plan;
  const sources = trace.sources ?? [];
  const [memories, setMemories] = React.useState<MemoryItem[]>([]);

  const refresh = React.useCallback(async () => {
    if (!workspaceId) {
      setMemories([]);
      return;
    }
    try {
      setMemories(await api.memory.list(workspaceId));
    } catch {
      /* keep previous on transient error */
    }
  }, [workspaceId]);

  // Refresh on workspace change and after each answered turn (memory may have updated).
  React.useEffect(() => {
    refresh();
  }, [refresh, trace.plan]);

  const weakTopics = memories.filter((m) => m.kind === "weak_topic");
  const profile = memories.filter((m) => m.kind !== "weak_topic");

  return (
    <aside className="hidden w-72 shrink-0 flex-col overflow-y-auto border-l border-border bg-card/40 lg:flex">
      <Section icon={<Sparkles className="size-3.5" />} title="Planner">
        {plan ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1">
              {plan.tools.length > 0 ? (
                plan.tools.map((t) => (
                  <span
                    key={t}
                    className="rounded border border-border bg-card px-1.5 py-0.5 font-mono text-[10px] text-foreground/80"
                  >
                    {t}
                  </span>
                ))
              ) : (
                <Placeholder>Answered directly (no tools).</Placeholder>
              )}
            </div>
            {plan.reasoning && (
              <p className="text-xs leading-relaxed text-muted-foreground">
                {plan.reasoning}
              </p>
            )}
          </div>
        ) : (
          <Placeholder>The planner&apos;s decision appears here as it answers.</Placeholder>
        )}
      </Section>

      <Section icon={<BookOpen className="size-3.5" />} title="Sources">
        {sources.length > 0 ? (
          <ul className="space-y-2">
            {sources.map((s) => (
              <li key={s.index} className="rounded-md border border-border bg-card p-2">
                <div className="mb-1 flex items-center gap-1.5 text-xs">
                  <span className="text-accent">[{s.index}]</span>
                  {s.kind === "web" ? (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 truncate font-medium text-foreground/90 underline decoration-border underline-offset-2 hover:decoration-accent"
                    >
                      {s.title}
                    </a>
                  ) : (
                    <span className="flex-1 truncate font-medium text-foreground/90">
                      {s.filename}
                    </span>
                  )}
                  <span className="shrink-0 rounded bg-secondary px-1 text-[9px] uppercase text-muted-foreground">
                    {s.kind === "web" ? "web" : s.page ? `p.${s.page}` : "note"}
                  </span>
                </div>
                <p className="line-clamp-3 text-[11px] leading-relaxed text-muted-foreground">
                  {s.snippet}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <Placeholder>
            Retrieved documents and citations appear here when the agent answers.
          </Placeholder>
        )}
      </Section>

      <Section icon={<TriangleAlert className="size-3.5" />} title="Weak topics">
        {weakTopics.length > 0 ? (
          <ul className="space-y-1">
            {weakTopics.map((m) => (
              <li
                key={m.id}
                className="flex items-center justify-between gap-2 rounded-md border border-border bg-card px-2 py-1 text-xs"
              >
                <span className="truncate text-foreground/90">{m.topic}</span>
                <span
                  className="shrink-0 rounded-full bg-destructive/15 px-1.5 py-0.5 text-[10px] text-destructive"
                  title={`Missed ${m.weight} time(s)`}
                >
                  ×{m.weight}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <Placeholder>
            Topics you miss most (from quizzes &amp; interviews) will be prioritized here.
          </Placeholder>
        )}
      </Section>

      <Section icon={<Brain className="size-3.5" />} title="Memory">
        {profile.length > 0 ? (
          <ul className="space-y-1.5">
            {profile.map((m) => (
              <li
                key={m.id}
                className="rounded-md border border-border bg-card px-2 py-1.5 text-[11px] leading-relaxed text-muted-foreground"
              >
                {m.content}
              </li>
            ))}
          </ul>
        ) : (
          <Placeholder>Preferences and facts the planner remembers about you.</Placeholder>
        )}
      </Section>

      <Section icon={<UploadCloud className="size-3.5" />} title="Upload status">
        <Placeholder>Live processing status for uploaded documents.</Placeholder>
      </Section>
    </aside>
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-b border-border px-3 py-3 last:border-b-0">
      <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {icon}
        {title}
      </div>
      {children}
    </div>
  );
}

function Placeholder({ children }: { children: React.ReactNode }) {
  return <p className="text-xs leading-relaxed text-muted-foreground/70">{children}</p>;
}
