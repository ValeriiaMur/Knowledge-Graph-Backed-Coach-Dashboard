import { useState } from "react";
import { buildAccordions } from "../derive";
import { Icons, iconByName } from "../icons";
import type { MemberProfile } from "../types";

type Props = { member: MemberProfile };

export function AccordionCard({ member }: Props): JSX.Element {
  const sections = buildAccordions(member);
  const [open, setOpen] = useState<boolean[]>(() => sections.map((s) => s.open));
  const toggle = (i: number): void => {
    setOpen((o) => o.map((v, k) => (k === i ? !v : v)));
  };
  return (
    <div className="c c-pad g-accord rise" style={{ animationDelay: ".1s" }}>
      {sections.map((a, i) => (
        <div key={a.title} className={"acc-row" + (open[i] ? " open" : "")}>
          <div className="acc-head" onClick={() => toggle(i)}>
            <span className="t">{a.title}</span>
            <span className="acc-chev">
              <Icons.chevron size={18} />
            </span>
          </div>
          <div className="acc-body">
            {a.items.map((g) => {
              const Ic = iconByName(g.ic);
              return (
                <div key={g.nm} className="gear-item">
                  <span className="gear-ic">
                    <Ic size={20} />
                  </span>
                  <div style={{ minWidth: 0 }}>
                    <div className="nm">{g.nm}</div>
                    <div className="sub">{g.sub}</div>
                  </div>
                  <span className="gear-dots">
                    <Icons.dots size={18} />
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
