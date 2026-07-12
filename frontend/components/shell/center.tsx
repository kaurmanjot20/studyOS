import {
  ClipboardList,
  FileUser,
  MessageSquare,
  Mic,
  NotebookPen,
  SquareStack,
} from "lucide-react";

import { ChatView, type Trace } from "@/components/chat/chat-view";
import { InterviewView } from "@/components/interview/interview-view";
import { ResumeView } from "@/components/interview/resume-view";
import { FlashcardsView } from "@/components/study/flashcards-view";
import { QuizView } from "@/components/study/quiz-view";
import { RevisionView } from "@/components/study/revision-view";
import { cn } from "@/lib/utils";
import type { Workspace } from "@/lib/types";

export type WorkspaceMode =
  | "chat"
  | "interview"
  | "resume"
  | "quiz"
  | "revision"
  | "flashcards";

const MODES: { id: WorkspaceMode; label: string; icon: React.ReactNode }[] = [
  { id: "chat", label: "Chat", icon: <MessageSquare className="size-3.5" /> },
  { id: "interview", label: "Interview", icon: <Mic className="size-3.5" /> },
  { id: "resume", label: "Resume", icon: <FileUser className="size-3.5" /> },
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
      ) : mode === "interview" ? (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <InterviewView workspaceId={workspace.id} />
        </div>
      ) : mode === "resume" ? (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <ResumeView workspaceId={workspace.id} />
        </div>
      ) : mode === "quiz" ? (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <QuizView workspaceId={workspace.id} />
        </div>
      ) : mode === "flashcards" ? (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <FlashcardsView workspaceId={workspace.id} />
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <RevisionView workspaceId={workspace.id} />
        </div>
      )}
    </main>
  );
}
