"""Workout generation orchestrator.

Pipeline (every step traced): derive constraints → resolve concepts →
safety filter (deterministic) → LLM composes from allowed candidates only →
validate plan against allowed set → assemble provenance.

`llm` is injectable: tests pass a fake; production uses anthropic_compose
(app/runtime/anthropic_llm.py). A plan referencing any filtered exercise is
rejected — the model cannot un-filter."""

import logging
import time
from collections.abc import Callable

from app.graph.movement_kg import build_movement_graph
from app.runtime.constraints import derive_constraints
from app.runtime.schemas import (
    GenerationResult,
    PlanItem,
    Provenance,
    Trace,
    TraceEvent,
    WorkoutPlan,
)
from app.safety.filter import apply_safety_filter

logger = logging.getLogger(__name__)

LlmFn = Callable[[dict], dict]


def _timed(trace: Trace, step: str, fn: Callable, **detail):
    start = time.perf_counter()
    out = fn()
    ms = (time.perf_counter() - start) * 1000
    trace.events.append(TraceEvent(step=step, ms=round(ms, 2), detail=detail))
    logger.info("trace step=%s ms=%.1f %s", step, ms, detail)
    return out


def generate_workout(
    prompt: str,
    minutes: int,
    llm: LlmFn,
    use_member_context: bool = True,
) -> GenerationResult:
    trace = Trace()
    g = build_movement_graph()

    derived = _timed(
        trace, "resolve_concepts", lambda: derive_constraints(prompt, use_member_context)
    )
    result = _timed(
        trace,
        "safety_filter",
        lambda: apply_safety_filter(derived.constraints),
        injured=derived.constraints.injured_joints,
        excluded=derived.constraints.excluded_terms,
    )

    provenance = Provenance(
        resolved_concepts=derived.resolved_concepts,
        unresolved=derived.unresolved,
        removed=result.removed,
        allowed_count=len(result.allowed),
        down_ranked=[e.name for e in result.allowed if e.down_ranked],
    )

    if not result.allowed:
        return GenerationResult(
            plan=None,
            provenance=provenance,
            trace=trace,
            error="Safety filtering removed every exercise — relax a constraint.",
        )

    payload = {
        "prompt": prompt,
        "minutes": minutes,
        "candidates": [
            {
                "node_id": e.node_id,
                "name": e.name,
                "priority_tier": e.priority_tier,
                "down_ranked": e.down_ranked,
            }
            for e in sorted(result.allowed, key=lambda e: (e.down_ranked, e.priority_tier))
        ],
        "removed": [{"node_id": r.node_id, "reason": r.reason} for r in result.removed],
    }

    raw = _timed(trace, "compose_plan", lambda: llm(payload), candidates=len(result.allowed))

    allowed_ids = {e.node_id for e in result.allowed}
    try:
        plan = _validate(raw, allowed_ids, g)
    except ValueError as exc:
        logger.warning("plan rejected: %s", exc)
        return GenerationResult(plan=None, provenance=provenance, trace=trace, error=str(exc))

    return GenerationResult(plan=plan, provenance=provenance, trace=trace)


def _validate(raw: dict, allowed_ids: set[str], g) -> WorkoutPlan:
    sections: dict[str, list[PlanItem]] = {}
    for section in ("warmup", "main", "cooldown"):
        items = []
        for entry in raw.get(section, []):
            ex = entry.get("exercise")
            if ex not in allowed_ids:
                raise ValueError(
                    f"Composer returned '{ex}' in {section}, which is not in the "
                    "safety-allowed set — plan rejected."
                )
            items.append(
                PlanItem(
                    exercise=ex,
                    name=g.nodes[ex]["name"],
                    sets=int(entry.get("sets", 3)),
                    reps=entry.get("reps"),
                    duration_sec=entry.get("duration_sec"),
                    rest_sec=int(entry.get("rest_sec", 60)),
                )
            )
        sections[section] = items
    if not sections["main"]:
        raise ValueError("Composer returned an empty main section — plan rejected.")
    return WorkoutPlan(**sections)
