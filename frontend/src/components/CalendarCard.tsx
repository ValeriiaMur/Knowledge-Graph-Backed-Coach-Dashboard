import { Fragment } from "react";
import { buildCalendar } from "../derive";
import type { MemberProfile } from "../types";

type Props = { member: MemberProfile; now: Date };

const SLOT = 64; // px per time slot row

export function CalendarCard({ member, now }: Props): JSX.Element {
  const calendar = buildCalendar(member, now);
  const [prev, cur, next] = calendar.months;
  return (
    <div className="c c-pad g-calendar rise" style={{ animationDelay: ".16s" }}>
      <div className="cal-top">
        <button className="monthpill">{prev?.m}</button>
        <span className="cal-month">{cur?.m}</span>
        <button className="monthpill">{next?.m}</button>
      </div>
      <div className="cal-grid">
        <div></div>
        {calendar.days.map((d) => (
          <div key={d.n} className={"cal-dh" + (d.today ? " today" : "")}>
            <div className="d">{d.d}</div>
            <div className="n">{d.n}</div>
          </div>
        ))}
        {calendar.times.map((t, r) => (
          <Fragment key={t}>
            <div className="cal-time">{t}</div>
            {calendar.days.map((d, c) => {
              const ev = calendar.events.find((e) => e.col === c + 1 && e.row === r);
              return (
                <div key={d.n} className="cal-cell" style={{ height: SLOT }}>
                  {ev ? (
                    <div
                      className={"evt " + ev.theme}
                      style={{ top: 6, height: ev.span * SLOT - 12 }}
                    >
                      <div className="et">{ev.t}</div>
                      <div className="es">{ev.s}</div>
                      <div className="evt-faces">
                        {ev.faces.map((f) => (
                          <span key={f} className="face">
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
    </div>
  );
}
