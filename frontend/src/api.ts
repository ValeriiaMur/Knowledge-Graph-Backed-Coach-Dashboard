import type {
  ChatHistoryItem,
  ChatReply,
  GenerationResult,
  GraphData,
  MemberProfile,
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

export const api = {
  member: () => get<MemberProfile>("/api/member"),
  generate: (prompt: string, minutes: number) =>
    post<GenerationResult>("/api/generate", { prompt, minutes }),
  chat: (message: string, sessionId: string) =>
    post<ChatReply>("/api/copilot/chat", { message, session_id: sessionId }),
  quickPrompts: () => get<string[]>("/api/copilot/quick-prompts"),
  chatHistory: () => get<ChatHistoryItem[]>("/api/copilot/chat-history"),
  timeseries: (metric: string) => get<Timeseries>(`/api/member/timeseries/${metric}`),
  graph: () => get<GraphData>("/api/graph"),
};
