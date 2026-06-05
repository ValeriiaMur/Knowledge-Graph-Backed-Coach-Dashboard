import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { ChatBubble, type Message } from "./ChatBubble";
import { QuickPrompts } from "./QuickPrompts";

let nextId = 1;

/** Chart prompts render deterministically from the timeseries endpoints —
 * no LLM round-trip for a known chart (fast + always grounded). */
const CHART_PROMPTS: Record<string, string> = {
  "plot adherence trend": "adherence",
  "compare last 4 weeks": "adherence",
  "sleep this week": "sleep",
};

export function CopilotPanel(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void api
      .quickPrompts()
      .then(setPrompts)
      .catch(() => setPrompts([]));
    void api
      .chatHistory()
      .then((hist) =>
        setMessages(
          hist.map((h) => ({
            id: nextId++,
            from: h.from === "member" ? "member" : "ai",
            text: h.text,
            ts: h.ts.slice(0, 16).replace("T", " "),
          })),
        ),
      )
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [messages]);

  const send = async (text: string): Promise<void> => {
    setMessages((m) => [...m, { id: nextId++, from: "coach", text }]);
    setInput("");

    const chartMetric = CHART_PROMPTS[text.toLowerCase()];
    if (chartMetric) {
      const series = await api.timeseries(chartMetric);
      setMessages((m) => [
        ...m,
        { id: nextId++, from: "ai", text: `Here's the ${chartMetric} trend:`, chart: series },
      ]);
      return;
    }
    if (text.toLowerCase() === "show message pattern") {
      const hist = await api.chatHistory();
      const byDay = new Map<string, number>();
      for (const h of hist) byDay.set(h.ts.slice(0, 10), (byDay.get(h.ts.slice(0, 10)) ?? 0) + 1);
      const series = {
        metric: "messages per day",
        unit: "count",
        points: [...byDay.entries()].map(([x, y]) => ({ x, y })),
      };
      setMessages((m) => [
        ...m,
        { id: nextId++, from: "ai", text: "Message pattern:", chart: series },
      ]);
      return;
    }

    setBusy(true);
    try {
      const reply = await api.chat(text, "coach-session");
      setMessages((m) => [
        ...m,
        { id: nextId++, from: "ai", text: reply.reply, toolCalls: reply.tool_calls },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          id: nextId++,
          from: "ai",
          text: `Copilot unavailable: ${e instanceof Error ? e.message : "error"}. Is ANTHROPIC_API_KEY set?`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <h2>Coach copilot</h2>
      <QuickPrompts prompts={prompts} onPick={(p) => void send(p)} disabled={busy} />
      <div className="chat-log" ref={logRef}>
        {messages.map((m) => (
          <ChatBubble key={m.id} msg={m} />
        ))}
        {busy && <div className="bubble bubble-ai">…</div>}
      </div>
      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && input && !busy && void send(input)}
          placeholder="Ask about this member…"
        />
        <button className="btn" disabled={busy || !input} onClick={() => void send(input)}>
          Send
        </button>
      </div>
    </div>
  );
}
