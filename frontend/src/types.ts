/** Mirrors backend Pydantic contracts (CLAUDE.md §1: typed end-to-end). */

export type PlanItem = {
  exercise: string;
  name: string;
  sets: number;
  reps: number | null;
  duration_sec: number | null;
  rest_sec: number;
};

export type WorkoutPlan = {
  warmup: PlanItem[];
  main: PlanItem[];
  cooldown: PlanItem[];
};

export type ResolvedConcept = {
  query: string;
  node_id: string | null;
  method: string;
  confidence: number;
  passes_tried: string[];
};

export type RemovedExercise = {
  node_id: string;
  name: string;
  reason: string;
  graph_path: string;
  substitutes: string[];
};

export type Provenance = {
  resolved_concepts: ResolvedConcept[];
  unresolved: string[];
  removed: RemovedExercise[];
  allowed_count: number;
  down_ranked: string[];
};

export type TraceEvent = { step: string; ms: number; detail: Record<string, unknown> };

export type GenerationResult = {
  plan: WorkoutPlan | null;
  provenance: Provenance;
  trace: { events: TraceEvent[] };
  error: string | null;
};

export type ChatReply = { reply: string; tool_calls: string[]; error: string | null };

export type TimeseriesPoint = { x: string; y: number };
export type Timeseries = {
  metric: string;
  unit?: string;
  points: TimeseriesPoint[];
  error?: string;
};

export type Goal = {
  id: string;
  priority: number;
  target_date: string | null;
  text: string;
};

export type Preferences = {
  training_days_per_week: number;
  preferred_days: string[];
  preferred_session_minutes: number;
  dislikes: string[];
  notes: string;
};

export type WorkoutHistoryItem = {
  date: string;
  title: string;
  planned: boolean;
  completed: boolean;
  duration_min: number;
  rpe: number | null;
  exercises: string[];
};

export type AdherenceWeek = { week_of: string; pct: number };
export type Adherence = { trend: string; weekly_completion_pct: AdherenceWeek[] };

export type Biomarkers = {
  hrv_ms: number;
  resting_hr_bpm: number;
  sleep_hours_last_7_days: number[];
  weight_trend_kg: { date: string; kg: number }[];
};

export type MemberProfile = {
  profile: {
    id: string;
    name: string;
    age: number;
    sex: string;
    tier?: string;
    member_since?: string;
  };
  goals: Goal[];
  preferences: Preferences;
  injuries: { region: string; status: string; severity: string; notes: string }[];
  equipment_available: string[];
  workout_history: WorkoutHistoryItem[];
  adherence: Adherence;
  biomarkers: Biomarkers;
  coach_brief: {
    generated_for: string;
    morning_tasks: { type: string; text: string }[];
    churn_risk: { level: string; reasons: string[] };
  };
};

export type ChatHistoryItem = { ts: string; from: string; text: string };

export type GraphNode = { id: string; kind: string; name: string };
export type GraphLink = { source: string; target: string; rel: string };
export type GraphData = { nodes: GraphNode[]; links: GraphLink[] };
