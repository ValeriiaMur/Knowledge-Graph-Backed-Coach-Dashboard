import type { ChatAttachment, Timeseries } from "../types";
import { Icons } from "../icons";
import { TrendChart } from "./TrendChart";

export type Message = {
  id: number;
  from: "coach" | "ai" | "member";
  text: string;
  toolCalls?: string[];
  chart?: Timeseries;
  ts?: string;
  attachments?: ChatAttachment[];
};

type Props = { msg: Message };

function Attachment({ att }: { att: ChatAttachment }): JSX.Element {
  // synthetic dataset ships captions, not files — render an image card;
  // real URLs (if present) render as the actual image.
  return (
    <div className="chat-att">
      {att.url ? (
        <img src={att.url} alt={att.caption ?? "attachment"} />
      ) : (
        <div className="chat-att-ph">
          <Icons.user size={22} />
        </div>
      )}
      <span className="chat-att-cap">
        {att.type}
        {att.caption ? ` · ${att.caption}` : ""}
      </span>
    </div>
  );
}

export function ChatBubble({ msg }: Props): JSX.Element {
  const cls = msg.from === "coach" ? "bubble bubble-coach" : "bubble bubble-ai";
  return (
    <div className={cls}>
      {msg.from === "member" && <div className="bubble-meta">member · {msg.ts}</div>}
      {msg.text || "…"}
      {msg.attachments?.map((att, i) => (
        <Attachment key={i} att={att} />
      ))}
      {msg.chart && <TrendChart series={msg.chart} />}
      {msg.toolCalls && msg.toolCalls.length > 0 && (
        <div className="bubble-meta">grounded via: {msg.toolCalls.join(", ")}</div>
      )}
    </div>
  );
}
