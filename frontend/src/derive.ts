/** Pure view-model derivations: real member context → designed dashboard widgets.
 * Everything rendered by the dashboard comes through here from /api/member or
 * /api/generate — no hardcoded member data. */

import type { GenerationResult, MemberProfile, WorkoutHistoryItem } from "./types";

export type SegStyle = "dark" | "accent" | "hatch" | "outline";

export type StatItem = { lab: string; val: string; style: SegStyle; grow?: boolean };
export type KpiItem = { icon: string; n: string; suffix?: string; label: string };
export type ProgressDay = { d: string; h: number; kind: "ink" | "muted" | "acc"; peak: boolean };
export type ProgressWeek = {
  total: string;
  unit: string;
  caption: string[];
  peakLabel: string;
  days: ProgressDay[];
};
export type ProgramSeg = { lab: string; val: string; style: SegStyle; flex: number };
export type Program = { title: string; pct: string; segs: ProgramSeg[] };
export type AccordionItem = { ic: string; nm: string; sub: string };
export type AccordionSection = { title: string; open: boolean; items: AccordionItem[] };
export type CalendarEvent = {
  col: number;
  row: number;
  span: number;
  theme: "dark" | "light";
  t: string;
  s: string;
  faces: string[];
};
export type CalendarModel = {
  months: { m: string; cur: boolean }[];
  days: { d: string; n: string; today: boolean }[];
  times: string[];
  events: CalendarEvent[];
};
export type SessionItem = { ic: string; nm: string; sub: string; done: boolean };
export type SessionModel = { title: string; items: SessionItem[] };

const DAY_LETTERS = ["S", "M", "T", "W", "T", "F", "S"] as const;
const DAY_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;
const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
] as const;

function isoDate(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function parseIso(s: string): Date {
  return new Date(`${s}T00:00:00`);
}

export function firstName(name: string): string {
  return name.split(" ")[0] ?? name;
}

export function initials(name: string): string {
  return name
    .split(" ")
    .map((w) => w.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function dayBadge(memberSince: string | undefined, now: Date): string {
  if (!memberSince) return "Member";
  const days = Math.max(
    1,
    Math.floor((now.getTime() - parseIso(memberSince).getTime()) / 86_400_000),
  );
  return `Day ${days}`;
}

/* ---- hero stat pills: adherence + biomarkers ---- */
export function buildStatbar(m: MemberProfile): StatItem[] {
  const weeks = m.adherence.weekly_completion_pct;
  const latest = weeks[weeks.length - 1];
  const sleep = m.biomarkers.sleep_hours_last_7_days;
  const sleepAvg = sleep.length > 0 ? sleep.reduce((a, b) => a + b, 0) / sleep.length : 0;
  return [
    { lab: "Adherence", val: latest ? `${latest.pct}%` : "—", style: "dark" },
    { lab: "HRV", val: `${m.biomarkers.hrv_ms} ms`, style: "accent" },
    {
      lab: "Sleep · last 7 days",
      val: `${sleepAvg.toFixed(1)} h avg (${m.adherence.trend} adherence)`,
      style: "hatch",
      grow: true,
    },
    { lab: "Resting HR", val: `${m.biomarkers.resting_hr_bpm} bpm`, style: "outline" },
  ];
}

/* ---- hero KPIs from workout history ---- */
export function buildKpis(m: MemberProfile): KpiItem[] {
  const completed = m.workout_history.filter((w) => w.completed);
  const minutes = completed.reduce((a, w) => a + w.duration_min, 0);
  const rpes = completed.map((w) => w.rpe).filter((r): r is number => r !== null);
  const avgRpe = rpes.length > 0 ? rpes.reduce((a, b) => a + b, 0) / rpes.length : 0;
  return [
    { icon: "dumbbell", n: String(completed.length), label: "Sessions" },
    { icon: "flame", n: String(minutes), suffix: " min", label: "Trained" },
    { icon: "bolt", n: avgRpe.toFixed(1), label: "Avg RPE" },
  ];
}

/* ---- weekly training-minutes bars (last 7 days ending today) ---- */
export function buildProgressWeek(history: WorkoutHistoryItem[], now: Date): ProgressWeek {
  const byDate = new Map<string, number>();
  for (const w of history) {
    if (w.completed) byDate.set(w.date, (byDate.get(w.date) ?? 0) + w.duration_min);
  }
  const days: { letter: string; minutes: number }[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 86_400_000);
    days.push({
      letter: DAY_LETTERS[d.getDay()] ?? "?",
      minutes: byDate.get(isoDate(d)) ?? 0,
    });
  }
  const max = Math.max(...days.map((d) => d.minutes));
  const total = days.reduce((a, d) => a + d.minutes, 0);
  const peakIdx = max > 0 ? days.findIndex((d) => d.minutes === max) : -1;
  const h = Math.floor(total / 60);
  const mm = total % 60;
  const peakH = Math.floor(max / 60);
  const peakM = max % 60;
  return {
    total: h > 0 ? `${h}.${String(Math.round((mm / 60) * 10))}` : String(mm),
    unit: h > 0 ? "h" : "min",
    caption: ["Training time", "last 7 days"],
    peakLabel: peakH > 0 ? `${peakH}h ${peakM}m` : `${peakM}m`,
    days: days.map((d, i) => ({
      d: d.letter,
      h: max > 0 ? Math.round((d.minutes / max) * 100) : 0,
      kind: i === peakIdx ? "acc" : d.minutes === 0 ? "muted" : "ink",
      peak: i === peakIdx,
    })),
  };
}

/* ---- adherence segments (the small % card) ---- */
export function buildProgram(m: MemberProfile): Program {
  const weeks = m.adherence.weekly_completion_pct;
  const latest = weeks[weeks.length - 1];
  const styles: SegStyle[] = ["accent", "dark", "outline"];
  const shown = weeks.slice(-3);
  return {
    title: "Adherence",
    pct: latest ? `${latest.pct}%` : "—",
    segs: shown.map((w, i) => {
      const d = parseIso(w.week_of);
      return {
        lab: `${MONTHS[d.getMonth()]?.slice(0, 3) ?? ""} ${d.getDate()}`,
        val: `${w.pct}%`,
        style: styles[i] ?? "outline",
        flex: Math.max(w.pct, 25),
      };
    }),
  };
}

/* ---- left accordion sections from real context ---- */
const EQUIPMENT_ICONS: [RegExp, string][] = [
  [/barbell/i, "barbell"],
  [/band/i, "band"],
  [/mat|yoga/i, "stretch"],
  [/bench/i, "plank"],
];

export function iconForEquipment(name: string): string {
  for (const [re, ic] of EQUIPMENT_ICONS) if (re.test(name)) return ic;
  return "dumbbell";
}

const EXERCISE_ICONS: [RegExp, string][] = [
  [/squat|wall sit/i, "squat"],
  [/deadlift|hinge|hip thrust/i, "dead"],
  [/lunge|step/i, "lunge"],
  [/row|pull/i, "row"],
  [/band/i, "band"],
  [/plank|bench|press/i, "plank"],
  [/raise|core|carry/i, "core"],
  [/stretch|mobility|cool|warm/i, "stretch"],
];

export function iconForExercise(name: string): string {
  for (const [re, ic] of EXERCISE_ICONS) if (re.test(name)) return ic;
  return "dumbbell";
}

export function buildAccordions(m: MemberProfile): AccordionSection[] {
  return [
    {
      title: "Equipment",
      open: true,
      items: m.equipment_available.map((e) => ({
        ic: iconForEquipment(e),
        nm: e,
        sub: "available at home",
      })),
    },
    {
      title: "Injuries",
      open: false,
      items: m.injuries.map((inj) => ({
        ic: "bell",
        nm: inj.region,
        sub: `${inj.status} · ${inj.severity}`,
      })),
    },
    {
      title: "Goals",
      open: false,
      items: m.goals.map((g) => ({
        ic: "bolt",
        nm: g.text,
        sub: g.target_date ? `target ${g.target_date}` : `priority ${g.priority}`,
      })),
    },
    {
      title: "Preferences",
      open: false,
      items: [
        {
          ic: "clock",
          nm: `${m.preferences.training_days_per_week}×/week · ${m.preferences.preferred_session_minutes} min`,
          sub: m.preferences.preferred_days.join(" · "),
        },
        {
          ic: "dots",
          nm: "Dislikes",
          sub: m.preferences.dislikes.join(", ") || "none",
        },
      ],
    },
  ];
}

/* ---- weekly calendar from history + preferences + brief ---- */
export function buildCalendar(m: MemberProfile, now: Date): CalendarModel {
  // Monday-start week containing `now`, six columns Mon..Sat (as designed).
  const dow = now.getDay(); // 0=Sun
  const monday = new Date(now.getTime() - ((dow + 6) % 7) * 86_400_000);
  const week: Date[] = [];
  for (let i = 0; i < 6; i++) week.push(new Date(monday.getTime() + i * 86_400_000));

  const cur = MONTHS[now.getMonth()] ?? "";
  const prev = MONTHS[(now.getMonth() + 11) % 12] ?? "";
  const next = MONTHS[(now.getMonth() + 1) % 12] ?? "";

  const member = initials(m.profile.name);
  const events: CalendarEvent[] = [];
  const rowCycle = [1, 2, 0, 3];
  const colOf = (d: Date): number => week.findIndex((w) => isoDate(w) === isoDate(d)) + 1;

  m.workout_history.forEach((w) => {
    const col = colOf(parseIso(w.date));
    if (col < 1) return;
    events.push({
      col,
      row: rowCycle[events.length % rowCycle.length] ?? 0,
      span: 1.3,
      theme: w.completed ? "dark" : "light",
      t: w.title || "Session",
      s: w.completed ? `${w.duration_min} min${w.rpe !== null ? ` · RPE ${w.rpe}` : ""}` : "missed",
      faces: [member],
    });
  });

  // upcoming preferred training days (no logged session yet)
  const todayIso = isoDate(now);
  week.forEach((d, i) => {
    const short = DAY_SHORT[d.getDay()] ?? "";
    if (isoDate(d) <= todayIso) return;
    if (!m.preferences.preferred_days.includes(short)) return;
    events.push({
      col: i + 1,
      row: rowCycle[events.length % rowCycle.length] ?? 0,
      span: 1.1,
      theme: "light",
      t: "Planned session",
      s: `${m.preferences.preferred_session_minutes} min target`,
      faces: [member],
    });
  });

  // coach brief day
  const briefCol = colOf(parseIso(m.coach_brief.generated_for));
  if (briefCol >= 1) {
    events.push({
      col: briefCol,
      row: rowCycle[events.length % rowCycle.length] ?? 0,
      span: 1.1,
      theme: "light",
      t: "Coach check-in",
      s: `${m.coach_brief.morning_tasks.length} morning tasks`,
      faces: [member, "C"],
    });
  }

  return {
    months: [
      { m: prev, cur: false },
      { m: `${cur} ${now.getFullYear()}`, cur: true },
      { m: next, cur: false },
    ],
    days: week.map((d) => ({
      d: DAY_SHORT[d.getDay()] ?? "",
      n: String(d.getDate()),
      today: isoDate(d) === todayIso,
    })),
    times: ["6:00", "7:00", "8:00", "9:00", "10:00"],
    events,
  };
}

/* ---- dark session checklist: generated plan first, else latest workout ---- */
export function buildSession(
  generation: GenerationResult | null,
  m: MemberProfile,
): SessionModel | null {
  if (generation?.plan) {
    const { warmup, main, cooldown } = generation.plan;
    const items = [...warmup, ...main, ...cooldown].map((it) => ({
      ic: iconForExercise(it.name),
      nm: it.name,
      sub:
        it.reps !== null
          ? `${it.sets} × ${it.reps} · rest ${it.rest_sec}s`
          : `${it.sets} × ${it.duration_sec ?? 30}s · rest ${it.rest_sec}s`,
      done: false,
    }));
    return { title: "Generated session", items };
  }
  const latest = [...m.workout_history]
    .filter((w) => w.exercises.length > 0)
    .sort((a, b) => (a.date < b.date ? 1 : -1))[0];
  if (!latest) return null;
  return {
    title: latest.title || "Latest session",
    items: latest.exercises.map((name) => ({
      ic: iconForExercise(name),
      nm: name,
      sub: `${latest.date} · ${latest.duration_min} min`,
      done: latest.completed,
    })),
  };
}
