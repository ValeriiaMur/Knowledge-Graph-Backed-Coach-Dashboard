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

export type MemberProfile = {
  profile: { id: string; name: string; age: number; sex: string };
  injuries: { region: string; status: string; severity: string; notes: string }[];
  equipment_available: string[];
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
