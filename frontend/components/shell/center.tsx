import {
  ClipboardList,
  MessageSquare,
  Mic,
  NotebookPen,
  SquareStack,
} from "lucide-react";

import { ChatView, type Trace } from "@/components/chat/chat-view";
import { cn } from "@/lib/utils";
import type { Workspace } from "@/lib/types";

export type WorkspaceMode =
  | "chat"
  | "interview"
  | "quiz"
  | "revision"
  | "flashcards";

const MODES: { id: WorkspaceMode; label: string; icon: React.ReactNode }[] = [
  { id: "chat", label: "Chat", icon: <MessageSquare className="size-3.5" /> },
  { id: "interview", label: "Interview", icon: <Mic className="size-3.5" /> },
  { id: "quiz", label: "Quiz", icon: <ClipboardList className="size-3.5" /> },
  { id: "revision", label: "Revision", icon: <NotebookPen className="size-3.5" /> },
  {
    id: "flashcards",
    label: "Flashcards",
    icon: <SquareStack className="size-3.5" />,
  },
];

interface CenterProps {
  workspace: Workspace | null;
  mode: WorkspaceMode;
  onModeChange: (mode: WorkspaceMode) => void;
  onTrace: (trace: Trace) => void;
}

export function Center({ workspace, mode, onModeChange, onTrace }: CenterProps) {
  if (!workspace) {
    return (
      <main className="flex flex-1 items-center justify-center px-6">
        <div className="max-w-sm text-center">
          <h2 className="text-base font-medium">No workspace selected</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Pick a workspace on the left, or create one to start preparing.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex flex-1 flex-col overflow-hidden">
      <div className="flex items-center gap-1 border-b border-border px-3">
        {MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => onModeChange(m.id)}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-2.5 py-2.5 text-sm transition-colors",
              m.id === mode
                ? "border-accent text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {m.icon}
            {m.label}
          </button>
        ))}
      </div>

      {mode === "chat" ? (
        <ChatView workspaceId={workspace.id} onTrace={onTrace} />
      ) : (
        <div className="flex flex-1 items-center justify-center overflow-y-auto px-6 py-10">
          <ModePlaceholder mode={mode} workspace={workspace} />
        </div>
      )}
    </main>
  );
}

const MODE_COPY: Record<WorkspaceMode, { title: string; body: string }> = {
  chat: {
    title: "Planner-first chat",
    body: "Ask anything. The planner will decide whether to search your notes, the web, your resume, or memory before it answers — with citations.",
  },
  interview: {
    title: "Mock interview",
    body: "Pick a company, difficulty, and subject. The agent conducts the interview, evaluates answers, and tracks weak areas.",
  },
  quiz: {
    title: "Adaptive quiz",
    body: "Generate MCQs, short and long answers from your documents, with adaptive difficulty and no repeats.",
  },
  revision: {
    title: "Revision notes",
    body: "One-page summaries and last-minute cheat sheets, generated from your uploaded material.",
  },
  flashcards: {
    title: "Flashcards",
    body: "Spaced-repetition cards generated automatically from your notes.",
  },
};

function ModePlaceholder({
  mode,
  workspace,
}: {
  mode: WorkspaceMode;
  workspace: Workspace;
}) {
  const copy = MODE_COPY[mode];
  return (
    <div className="max-w-md text-center">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">
        {workspace.name}
      </div>
      <h2 className="mt-1 text-lg font-medium">{copy.title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {copy.body}
      </p>
      <p className="mt-4 text-xs text-muted-foreground/60">
        Arrives in an upcoming build phase.
      </p>
    </div>
  );
}
