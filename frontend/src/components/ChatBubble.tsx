import type { Timeseries } from "../types";
import { TrendChart } from "./TrendChart";

export type Message = {
  id: number;
  from: "coach" | "ai" | "member";
  text: string;
  toolCalls?: string[];
  chart?: Timeseries;
  ts?: string;
};

type Props = { msg: Message };

export function ChatBubble({ msg }: Props): JSX.Element {
  const cls = msg.from === "coach" ? "bubble bubble-coach" : "bubble bubble-ai";
  return (
    <div className={cls}>
      {msg.from === "member" && <div className="bubble-meta">member · {msg.ts}</div>}
      {msg.text}
      {msg.chart && <TrendChart series={msg.chart} />}
      {msg.toolCalls && msg.toolCalls.length > 0 && (
        <div className="bubble-meta">grounded via: {msg.toolCalls.join(", ")}</div>
      )}
    </div>
  );
}
