"use client";

import * as React from "react";
import { ArrowUp, Plus, Sparkles } from "lucide-react";

import { Markdown } from "@/components/chat/markdown";
import { Button } from "@/components/ui/button";
import { HistoryMenu } from "@/components/ui/history-menu";
import { api } from "@/lib/api";
import { streamChat } from "@/lib/chat-stream";
import { cn } from "@/lib/utils";
import type {
  ChatSessionRecord,
  ChatTurn,
  PlanTrace,
  Source,
} from "@/lib/types";

export interface Trace {
  plan?: PlanTrace | null;
  sources?: Source[];
}

interface ChatViewProps {
  workspaceId: string;
  onTrace: (trace: Trace) => void;
}

const SUGGESTIONS = [
  "Explain deadlocks and the Coffman conditions",
  "Quiz me on normalization in DBMS",
  "What is the difference between TCP and UDP?",
];

export function ChatView({ workspaceId, onTrace }: ChatViewProps) {
  const [turns, setTurns] = React.useState<ChatTurn[]>([]);
  const [input, setInput] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [sessions, setSessions] = React.useState<ChatSessionRecord[]>([]);
  const sessionId = React.useRef<string | null>(null);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const loadSessions = React.useCallback(async () => {
    try {
      setSessions(await api.chat.sessions(workspaceId));
    } catch {
      setSessions([]);
    }
  }, [workspaceId]);

  const newChat = React.useCallback(() => {
    setTurns([]);
    sessionId.current = null;
    onTrace({ plan: null, sources: [] });
  }, [onTrace]);

  // New workspace → fresh conversation + load its past sessions.
  React.useEffect(() => {
    newChat();
    loadSessions();
  }, [workspaceId, newChat, loadSessions]);

  const openSession = async (id: string) => {
    try {
      const messages = await api.chat.messages(id);
      sessionId.current = id;
      setTurns(
        messages.map((m) => ({
          role: m.role,
          content: m.content,
          plan: m.plan,
          sources: m.sources ?? [],
        })),
      );
      const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
      onTrace({
        plan: lastAssistant?.plan ?? null,
        sources: lastAssistant?.sources ?? [],
      });
    } catch {
      /* ignore */
    }
  };

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [turns]);

  const patchLast = React.useCallback((patch: Partial<ChatTurn>) => {
    setTurns((prev) => {
      const next = [...prev];
      const i = next.length - 1;
      next[i] = { ...next[i], ...patch };
      return next;
    });
  }, []);

  const send = async (text: string) => {
    const message = text.trim();
    if (!message || busy) return;
    setInput("");
    setBusy(true);
    onTrace({ plan: null, sources: [] });
    setTurns((prev) => [
      ...prev,
      { role: "user", content: message },
      { role: "assistant", content: "", streaming: true },
    ]);

    let plan: PlanTrace | null = null;
    let sources: Source[] = [];

    await streamChat(
      workspaceId,
      { message, session_id: sessionId.current },
      {
        onPlan: (p) => {
          plan = p;
          patchLast({ plan: p });
          onTrace({ plan: p, sources });
        },
        onSources: (s) => {
          sources = s;
          patchLast({ sources: s });
          onTrace({ plan, sources: s });
        },
        onToken: (t) =>
          setTurns((prev) => {
            const next = [...prev];
            const i = next.length - 1;
            next[i] = { ...next[i], content: next[i].content + t };
            return next;
          }),
        onError: (detail) => patchLast({ error: detail, streaming: false }),
        onDone: (info) => {
          const isNew = sessionId.current === null;
          sessionId.current = info.session_id;
          patchLast({ streaming: false });
          if (isNew) loadSessions();
        },
      },
    ).catch((e) => patchLast({ error: String(e), streaming: false }));

    setBusy(false);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center gap-2 border-b border-border px-3 py-1.5">
        <Button variant="ghost" size="sm" className="gap-1.5" onClick={newChat}>
          <Plus className="size-3.5" /> New chat
        </Button>
        <div className="ml-auto">
          <HistoryMenu
            items={sessions.map((s) => ({
              id: s.id,
              title: s.title || "Untitled chat",
              subtitle: new Date(s.created_at).toLocaleString(),
            }))}
            activeId={sessionId.current}
            onOpen={openSession}
            onRename={async (id, title) => {
              await api.chat.rename(id, title);
              loadSessions();
            }}
            onDelete={async (id) => {
              await api.chat.remove(id);
              if (sessionId.current === id) newChat();
              loadSessions();
            }}
          />
        </div>
      </div>

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-6">
          {turns.length === 0 ? (
            <EmptyState onPick={send} />
          ) : (
            <div className="space-y-6">
              {turns.map((turn, i) => (
                <TurnView key={i} turn={turn} />
              ))}
            </div>
          )}
        </div>
      </div>

      <Composer
        value={input}
        busy={busy}
        onChange={setInput}
        onSend={() => send(input)}
      />
    </div>
  );
}

function TurnView({ turn }: { turn: ChatTurn }) {
  if (turn.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-lg rounded-br-sm bg-secondary px-3 py-2 text-sm">
          {turn.content}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {turn.plan && turn.plan.tools.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
          <Sparkles className="size-3 text-accent" />
          <span>Planned:</span>
          {turn.plan.tools.map((t) => (
            <span
              key={t}
              className="rounded border border-border bg-card px-1.5 py-0.5 font-mono text-[10px]"
            >
              {t}
            </span>
          ))}
        </div>
      )}

      {turn.content ? (
        <Markdown>{turn.content}</Markdown>
      ) : turn.streaming && !turn.error ? (
        <ThinkingDots />
      ) : null}

      {turn.error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {turn.error}
        </div>
      )}

      {turn.sources && turn.sources.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {turn.sources.map((s) =>
            s.kind === "web" ? (
              <a
                key={s.index}
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                title={s.snippet}
                className="inline-flex items-center gap-1 rounded border border-border bg-card px-1.5 py-0.5 text-[11px] text-muted-foreground hover:border-accent/50"
              >
                <span className="text-accent">[{s.index}]</span>
                <span className="rounded bg-secondary px-1 text-[9px] uppercase">web</span>
                <span className="max-w-[160px] truncate">{s.title}</span>
              </a>
            ) : (
              <span
                key={s.index}
                title={s.snippet}
                className="inline-flex items-center gap-1 rounded border border-border bg-card px-1.5 py-0.5 text-[11px] text-muted-foreground"
              >
                <span className="text-accent">[{s.index}]</span>
                <span className="max-w-[160px] truncate">{s.filename}</span>
                {s.page && <span className="opacity-60">p.{s.page}</span>}
              </span>
            ),
          )}
        </div>
      )}
    </div>
  );
}

function ThinkingDots() {
  return (
    <div className="flex gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="size-1.5 animate-pulse rounded-full bg-muted-foreground/60"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (t: string) => void }) {
  return (
    <div className="mx-auto mt-16 max-w-md text-center">
      <div className="mb-3 inline-flex size-9 items-center justify-center rounded-lg bg-accent/15 text-accent">
        <Sparkles className="size-4" />
      </div>
      <h2 className="text-base font-medium">Ask anything about your material</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        The planner decides what to retrieve before it answers — grounded in your notes,
        with citations.
      </p>
      <div className="mt-4 space-y-1.5">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="block w-full rounded-md border border-border bg-card px-3 py-2 text-left text-sm text-muted-foreground hover:border-muted-foreground/40 hover:text-foreground"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

function Composer({
  value,
  busy,
  onChange,
  onSend,
}: {
  value: string;
  busy: boolean;
  onChange: (v: string) => void;
  onSend: () => void;
}) {
  return (
    <div className="shrink-0 border-t border-border bg-background px-4 py-3">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          rows={1}
          placeholder="Ask a question…  (Enter to send, Shift+Enter for a new line)"
          className="max-h-40 flex-1 resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background"
        />
        <Button
          variant="accent"
          size="icon"
          onClick={onSend}
          disabled={busy || !value.trim()}
          aria-label="Send"
        >
          <ArrowUp className="size-4" />
        </Button>
      </div>
    </div>
  );
}
