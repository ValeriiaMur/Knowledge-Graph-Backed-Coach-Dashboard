import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

type Props = { open: boolean; onClose: () => void; context?: string };

/** Friendly out-of-scope notice for decorative controls. Stays on brand by
 * letting the visitor play with the design system's accent tokens instead. */
const ACCENTS: { name: string; hex: string }[] = [
  { name: "amber", hex: "#f1ce46" },
  { name: "orange", hex: "#ff6b3d" },
  { name: "lime", hex: "#c7e85a" },
  { name: "sky", hex: "#7fc8ff" },
  { name: "violet", hex: "#b9a6ff" },
];

export function DemoModal({ open, onClose, context }: Props): JSX.Element | null {
  const [accent, setAccent] = useState<string>(
    () => document.documentElement.getAttribute("data-accent") ?? "amber",
  );

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const pick = (name: string): void => {
    document.documentElement.setAttribute("data-accent", name);
    setAccent(name);
  };

  // Portaled to <body> so the fixed overlay centers against the viewport — a
  // transformed ancestor (card animations) would otherwise trap position:fixed.
  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="card modal-card rise"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="brand" style={{ marginBottom: 14 }}>
          <span className="mark"></span> Future Coach
        </div>
        <span className="tag tag-accent">demo scope</span>
        <h3 className="modal-title">Not wired up — on purpose</h3>
        <p className="modal-copy">
          {context ? `“${context}” actions are` : "This control is"} outside this demo&apos;s focus:
          graph-driven safety filtering, provenance, and grounded retrieval. In the full product
          this would open item-level actions.
        </p>
        <div className="modal-swatch-row">
          <span className="eyebrow">Meanwhile — try an accent</span>
          <div className="modal-swatches">
            {ACCENTS.map((a) => (
              <button
                key={a.name}
                className={"swatch" + (accent === a.name ? " on" : "")}
                style={{ background: a.hex }}
                aria-label={`Accent ${a.name}`}
                onClick={() => pick(a.name)}
              />
            ))}
          </div>
        </div>
        <button className="pill pill-dark pill-lg" onClick={onClose}>
          Back to the demo
        </button>
      </div>
    </div>,
    document.body,
  );
}
