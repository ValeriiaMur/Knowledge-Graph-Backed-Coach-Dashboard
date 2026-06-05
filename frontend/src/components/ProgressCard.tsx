import { useEffect, useState } from "react";
import { buildProgressWeek } from "../derive";
import { Icons } from "../icons";
import type { WorkoutHistoryItem } from "../types";

type Props = { history: WorkoutHistoryItem[]; now: Date };

export function ProgressCard({ history, now }: Props): JSX.Element {
  const progress = buildProgressWeek(history, now);
  const [grown, setGrown] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setGrown(true), 120);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="c c-pad g-progress rise" style={{ height: "100%", animationDelay: ".08s" }}>
      <div className="card-head">
        <span className="card-title">Progress</span>
        <button className="expand" aria-label="Expand">
          <Icons.arrowUR size={18} />
        </button>
      </div>
      <div className="bigtime">
        <span className="n">
          {progress.total}
          <span style={{ fontSize: 24, fontWeight: 600 }}> {progress.unit}</span>
        </span>
        <span className="lab">
          {progress.caption.map((l) => (
            <div key={l}>{l}</div>
          ))}
        </span>
      </div>
      <div className="bars">
        {progress.days.map((d, i) => (
          <div key={i} className={"barcol" + (d.peak ? " peak" : "")}>
            {d.peak ? (
              <div
                className="bubble"
                style={{ opacity: grown ? 1 : 0, transition: "opacity .5s .6s" }}
              >
                {progress.peakLabel}
              </div>
            ) : null}
            <div className="bartrack">
              <div
                className={"bar " + (d.kind === "muted" ? "muted2" : d.kind === "acc" ? "acc" : "")}
                style={{ height: grown ? `${d.h}%` : 0, transitionDelay: `${i * 60}ms` }}
              />
            </div>
            <div className="barlab">{d.d}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
