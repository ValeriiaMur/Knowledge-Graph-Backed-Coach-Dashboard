import type {
  ChatHistoryItem,
  ChatReply,
  GenerationResult,
  GraphData,
  MemberProfile,
  StreamEvent,
  Timeseries,
} from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

/** POST to the SSE endpoint and surface each `data:` frame as a typed event. */
async function chatStream(
  message: string,
  sessionId: string,
  onEvent: (ev: StreamEvent) => void,
): Promise<void> {
  const res = await fetch("/api/copilot/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok || !res.body) throw new Error(`/api/copilot/chat/stream: ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep = buffer.indexOf("\n\n");
    while (sep >= 0) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const data = frame
        .split("\n")
        .find((line) => line.startsWith("data: "))
        ?.slice(6);
      if (data) onEvent(JSON.parse(data) as StreamEvent);
      sep = buffer.indexOf("\n\n");
    }
  }
}

export const api = {
  member: () => get<MemberProfile>("/api/member"),
  generate: (prompt: string, minutes: number) =>
    post<GenerationResult>("/api/generate", { prompt, minutes }),
  chat: (message: string, sessionId: string) =>
    post<ChatReply>("/api/copilot/chat", { message, session_id: sessionId }),
  chatStream,
  quickPrompts: () => get<string[]>("/api/copilot/quick-prompts"),
  chatHistory: () => get<ChatHistoryItem[]>("/api/copilot/chat-history"),
  timeseries: (metric: string) => get<Timeseries>(`/api/member/timeseries/${metric}`),
  graph: () => get<GraphData>("/api/graph"),
};
