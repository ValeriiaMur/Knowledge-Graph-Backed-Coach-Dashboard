import { useEffect, useRef, useState } from "react";
import { Icons } from "../icons";

type Props = { targetMinutes: number };

/** Live workout timer; target length comes from the member's preferred
 * session minutes (real preference data, not a mock constant). */
export function TimerCard({ targetMinutes }: Props): JSX.Element {
  const targetSeconds = targetMinutes * 60;
  const [elapsed, setElapsed] = useState<number>(() => {
    const v = parseInt(localStorage.getItem("fc-timer") ?? "", 10);
    return Number.isFinite(v) ? v : 0;
  });
  const [running, setRunning] = useState(false);
  const ref = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!running) return;
    ref.current = window.setInterval(() => setElapsed((e) => Math.min(e + 1, targetSeconds)), 1000);
    return () => clearInterval(ref.current);
  }, [running, targetSeconds]);
  useEffect(() => {
    localStorage.setItem("fc-timer", String(elapsed));
  }, [elapsed]);

  const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const ss = String(elapsed % 60).padStart(2, "0");
  const frac = Math.min(elapsed / targetSeconds, 1);
  const R = 92;
  const C = 2 * Math.PI * R;

  return (
    <div className="c c-pad g-timer rise" style={{ height: "100%", animationDelay: ".12s" }}>
      <div className="card-head">
        <span className="card-title">Time tracker</span>
        <button className="expand" aria-label="Expand">
          <Icons.arrowUR size={18} />
        </button>
      </div>
      <div className="timer-wrap">
        <div className="ring-box">
          <svg width="220" height="220" viewBox="0 0 220 220">
            <circle cx="110" cy="110" r={R} fill="none" stroke="var(--chip)" strokeWidth="15" />
            <circle
              cx="110"
              cy="110"
              r={R}
              fill="none"
              stroke="var(--accent)"
              strokeWidth="15"
              strokeLinecap="round"
              strokeDasharray={C}
              strokeDashoffset={C * (1 - frac)}
              transform="rotate(-90 110 110)"
              style={{ transition: "stroke-dashoffset .9s linear" }}
            />
            {Array.from({ length: 60 }).map((_, i) => {
              const a = (i / 60) * Math.PI * 2 - Math.PI / 2;
              const r1 = 73;
              const r2 = i % 5 === 0 ? 67 : 70;
              return (
                <line
                  key={i}
                  x1={110 + Math.cos(a) * r1}
                  y1={110 + Math.sin(a) * r1}
                  x2={110 + Math.cos(a) * r2}
                  y2={110 + Math.sin(a) * r2}
                  stroke="var(--line)"
                  strokeWidth={i % 5 === 0 ? 1.4 : 0.8}
                />
              );
            })}
          </svg>
          <div className="center">
            <div className="ring-time">
              {mm}:{ss}
            </div>
            <div className="ring-sub">of {targetMinutes} min</div>
          </div>
        </div>
        <div className="timer-ctrls">
          <button
            className="tbtn"
            aria-label="Reset"
            onClick={() => {
              setRunning(false);
              setElapsed(0);
            }}
          >
            <Icons.reset size={20} />
          </button>
          <button
            className="tbtn primary"
            aria-label="Play / pause"
            onClick={() => setRunning((r) => !r)}
          >
            {running ? <Icons.pause size={22} /> : <Icons.play size={22} />}
          </button>
          <button className="tbtn dark" aria-label="History">
            <Icons.clock size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
