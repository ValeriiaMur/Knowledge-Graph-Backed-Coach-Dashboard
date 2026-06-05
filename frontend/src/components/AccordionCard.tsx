import { buildAccordions } from "../derive";
import { Icons, iconByName } from "../icons";
import type { MemberProfile } from "../types";

type Props = { member: MemberProfile; onDemo: (context: string) => void };

/** Member-context sections (equipment / injuries / goals / preferences) —
 * always open; everything shown comes from /api/member. */
export function AccordionCard({ member, onDemo }: Props): JSX.Element {
  const sections = buildAccordions(member);
  return (
    <div className="c c-pad g-accord rise" style={{ animationDelay: ".1s" }}>
      {sections.map((a) => (
        <div key={a.title} className="acc-row open">
          <div className="acc-head" style={{ cursor: "default" }}>
            <span className="t">{a.title}</span>
          </div>
          <div>
            {a.items.map((g) => {
              const Ic = iconByName(g.ic);
              return (
                <div key={g.nm} className="gear-item">
                  <span className="gear-ic">
                    <Ic size={20} />
                  </span>
                  <div style={{ minWidth: 0 }}>
                    <div className="nm">{g.nm}</div>
                    {g.sub && <div className="sub">{g.sub}</div>}
                  </div>
                  <button
                    className="gear-dots"
                    aria-label={`Actions for ${g.nm}`}
                    onClick={() => onDemo(g.nm)}
                  >
                    <Icons.dots size={18} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
