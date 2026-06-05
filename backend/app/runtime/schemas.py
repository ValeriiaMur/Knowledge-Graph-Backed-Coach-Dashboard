"""Typed contracts for the workout generator."""

from pydantic import BaseModel

from app.resolver.resolver import ResolvedConcept
from app.safety.filter import RemovedExercise


class PlanItem(BaseModel):
    exercise: str  # KG node id
    name: str = ""
    sets: int
    reps: int | None = None
    duration_sec: int | None = None
    rest_sec: int


class WorkoutPlan(BaseModel):
    warmup: list[PlanItem]
    main: list[PlanItem]
    cooldown: list[PlanItem]


class TraceEvent(BaseModel):
    step: str
    ms: float
    detail: dict = {}


class Trace(BaseModel):
    events: list[TraceEvent] = []


class SelectedExercise(BaseModel):
    """Why a plan item was chosen — the inclusion-side provenance
    (PROV-O style: the graph path is the prov:wasDerivedFrom justification)."""

    node_id: str
    name: str
    reason: str
    graph_path: str


class Provenance(BaseModel):
    """Why the plan looks the way it does — required for every generated plan."""

    resolved_concepts: list[ResolvedConcept]
    unresolved: list[str]
    removed: list[RemovedExercise]
    allowed_count: int
    down_ranked: list[str]
    selected: list[SelectedExercise] = []

    model_config = {"arbitrary_types_allowed": True}


class GenerationResult(BaseModel):
    plan: WorkoutPlan | None
    provenance: Provenance
    trace: Trace
    error: str | None = None

    model_config = {"arbitrary_types_allowed": True}
