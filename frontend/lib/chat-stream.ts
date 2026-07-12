/**
 * Consume the chat SSE stream.
 *
 * POSTs a message and parses the `event:`/`data:` frames the backend emits, dispatching
 * to typed callbacks. Uses fetch + a ReadableStream reader (EventSource can't POST).
 */
import type { PlanTrace, Source } from "@/lib/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface ChatStreamHandlers {
  onPlan?: (plan: PlanTrace) => void;
  onSources?: (sources: Source[]) => void;
  onToken?: (text: string) => void;
  onError?: (detail: string) => void;
  onDone?: (info: { session_id: string; message_id: string }) => void;
}

export async function streamChat(
  workspaceId: string,
  body: { message: string; session_id?: string | null },
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(
    `${BASE_URL}/api/workspaces/${workspaceId}/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    },
  );

  if (!res.ok || !res.body) {
    handlers.onError?.(`Request failed (${res.status}).`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line.
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      dispatch(frame, handlers);
    }
  }
}

function dispatch(frame: string, handlers: ChatStreamHandlers) {
  let event = "message";
  let data = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return;

  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    return;
  }

  switch (event) {
    case "plan":
      handlers.onPlan?.(parsed as PlanTrace);
      break;
    case "sources":
      handlers.onSources?.(parsed as Source[]);
      break;
    case "token":
      handlers.onToken?.((parsed as { text: string }).text);
      break;
    case "error":
      handlers.onError?.((parsed as { detail: string }).detail);
      break;
    case "done":
      handlers.onDone?.(parsed as { session_id: string; message_id: string });
      break;
  }
}
