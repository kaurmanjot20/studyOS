import { BookOpen, Brain, TriangleAlert, UploadCloud } from "lucide-react";

/** Right rail: retrieval sources, memory, weak topics, upload status. Filled in by
 * later phases; here it establishes the three-pane structure and its sections. */
export function RightSidebar() {
  return (
    <aside className="hidden w-72 shrink-0 flex-col border-l border-border bg-card/40 lg:flex">
      <Section icon={<BookOpen className="size-3.5" />} title="Sources">
        Retrieved documents and citations appear here when the agent answers.
      </Section>
      <Section icon={<Brain className="size-3.5" />} title="Memory">
        What the planner remembers about your preparation.
      </Section>
      <Section icon={<TriangleAlert className="size-3.5" />} title="Weak topics">
        Topics you miss most, prioritized for revision.
      </Section>
      <Section icon={<UploadCloud className="size-3.5" />} title="Upload status">
        Live processing status for uploaded documents.
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
      <p className="text-xs leading-relaxed text-muted-foreground/70">{children}</p>
    </div>
  );
}
