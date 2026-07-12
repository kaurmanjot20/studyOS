import { BookOpen, Brain, Sparkles, TriangleAlert, UploadCloud } from "lucide-react";

import type { Trace } from "@/components/chat/chat-view";

/** Right rail: the planner trace + retrieved sources for the current turn, plus memory /
 * weak-topics / upload placeholders filled in by later phases. */
export function RightSidebar({ trace }: { trace: Trace }) {
  const plan = trace.plan;
  const sources = trace.sources ?? [];

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
                <span className="text-xs text-muted-foreground/70">
                  Answered directly (no tools).
                </span>
              )}
            </div>
            {plan.reasoning && (
              <p className="text-xs leading-relaxed text-muted-foreground">
                {plan.reasoning}
              </p>
            )}
          </div>
        ) : (
          <Placeholder>The planner's decision appears here as it answers.</Placeholder>
        )}
      </Section>

      <Section icon={<BookOpen className="size-3.5" />} title="Sources">
        {sources.length > 0 ? (
          <ul className="space-y-2">
            {sources.map((s) => (
              <li key={s.index} className="rounded-md border border-border bg-card p-2">
                <div className="mb-1 flex items-center gap-1.5 text-xs">
                  <span className="text-accent">[{s.index}]</span>
                  <span className="flex-1 truncate font-medium text-foreground/90">
                    {s.filename}
                  </span>
                  {s.page && (
                    <span className="text-[10px] text-muted-foreground">p.{s.page}</span>
                  )}
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

      <Section icon={<Brain className="size-3.5" />} title="Memory">
        <Placeholder>What the planner remembers about your preparation.</Placeholder>
      </Section>
      <Section icon={<TriangleAlert className="size-3.5" />} title="Weak topics">
        <Placeholder>Topics you miss most, prioritized for revision.</Placeholder>
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
