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

    // token-level streaming (SSE), with a non-streaming fallback
    setBusy(true);
    const aiId = nextId++;
    setMessages((m) => [...m, { id: aiId, from: "ai", text: "" }]);
    const patch = (update: (msg: Message) => Message): void => {
      setMessages((m) => m.map((msg) => (msg.id === aiId ? update(msg) : msg)));
    };
    try {
      await api.chatStream(text, "coach-session", (ev) => {
        if (ev.type === "token") patch((msg) => ({ ...msg, text: msg.text + ev.text }));
        else if (ev.type === "tool")
          patch((msg) => ({ ...msg, toolCalls: [...(msg.toolCalls ?? []), ev.name] }));
        else if (ev.type === "done")
          patch((msg) => ({ ...msg, text: ev.reply, toolCalls: ev.tool_calls }));
        else if (ev.type === "error") throw new Error(ev.error);
      });
    } catch {
      try {
        const reply = await api.chat(text, "coach-session");
        patch((msg) => ({ ...msg, text: reply.reply, toolCalls: reply.tool_calls }));
      } catch (e) {
        patch((msg) => ({
          ...msg,
          text: `Copilot unavailable: ${e instanceof Error ? e.message : "error"}. Is ANTHROPIC_API_KEY set?`,
        }));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="c c-pad chat-card rise">
      <div className="card-head">
        <span className="card-title">Coach copilot</span>
        <span className="tag">grounded in member context</span>
      </div>
      <QuickPrompts prompts={prompts} onPick={(p) => void send(p)} disabled={busy} />
      <div className="chat-log no-sb" ref={logRef}>
        {messages.map((m) => (
          <ChatBubble key={m.id} msg={m} />
        ))}
      </div>
      <div className="chat-input">
        <input
          className="input-pill"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && input && !busy && void send(input)}
          placeholder="Ask about this member…"
        />
        <button
          className="pill pill-dark pill-lg"
          disabled={busy || !input}
          onClick={() => void send(input)}
        >
          Send
        </button>
      </div>
    </div>
  );
}
