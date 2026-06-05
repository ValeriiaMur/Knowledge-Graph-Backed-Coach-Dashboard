"""Phase 4 (red-green): agentic runtime — deterministic spine tested offline.
The LLM composer is injected; production wires Anthropic tool use."""

from app.runtime.constraints import derive_constraints
from app.runtime.generator import generate_workout
from app.runtime.schemas import PlanItem, WorkoutPlan

# --- constraint derivation ----------------------------------------------------


def test_member_constraints_come_from_kg2():
    """Injury + equipment must apply without the coach restating them."""
    c = derive_constraints("a solid lower body day", use_member_context=True)
    assert "joint:knee" in c.constraints.injured_joints
    assert "condition:patellofemoral pain syndrome" in c.constraints.conditions
    assert c.constraints.available_equipment is not None
    assert "equipment:Dumbbell" in c.constraints.available_equipment
    assert "equipment:Barbell" not in c.constraints.available_equipment


def test_prompt_concepts_resolved_and_recorded():
    c = derive_constraints("isolation around my pecs", use_member_context=False)
    assert any(r.node_id == "muscle:chest" for r in c.resolved_concepts)


def test_exclude_phrase_becomes_exclusion_constraint():
    c = derive_constraints("no deadlifts today please", use_member_context=False)
    assert "deadlift" in c.constraints.excluded_terms


def test_unresolved_terms_surface_not_silently_dropped():
    c = derive_constraints("avoid the flibbertigibbet", use_member_context=False)
    assert c.unresolved  # reported for the coach to clarify


# --- plan composition & validation ---------------------------------------------


def fake_llm(payload: dict) -> dict:
    """Deterministic composer: picks first allowed candidates."""
    ids = [c["node_id"] for c in payload["candidates"]]
    item = {"sets": 3, "reps": 10, "rest_sec": 60}
    return {
        "warmup": [{"exercise": ids[0], **item}],
        "main": [{"exercise": i, **item} for i in ids[1:4]],
        "cooldown": [{"exercise": ids[4], **item}],
    }


def test_generate_workout_returns_validated_plan():
    result = generate_workout("lower body, easy on the knee", minutes=30, llm=fake_llm)
    plan = result.plan
    assert isinstance(plan, WorkoutPlan)
    assert plan.main and plan.warmup and plan.cooldown
    assert all(isinstance(i, PlanItem) for i in plan.main)


def test_plan_cannot_contain_filtered_exercise():
    """If the composer returns a removed exercise, validation must reject it."""

    def malicious_llm(payload: dict) -> dict:
        removed_id = payload["removed"][0]["node_id"]
        item = {"sets": 3, "reps": 10, "rest_sec": 60}
        return {
            "warmup": [{"exercise": removed_id, **item}],
            "main": [{"exercise": removed_id, **item}],
            "cooldown": [{"exercise": removed_id, **item}],
        }

    result = generate_workout("lower body", minutes=30, llm=malicious_llm)
    assert result.error is not None
    assert result.plan is None


def test_provenance_trace_ships_with_plan():
    result = generate_workout("lower body, easy on the knee", minutes=30, llm=fake_llm)
    prov = result.provenance
    assert prov.resolved_concepts  # what the prompt mapped to
    assert prov.removed  # what safety filtered, with graph paths
    assert all(r.graph_path for r in prov.removed)
    assert prov.allowed_count + len(prov.removed) == 50


def test_trace_records_pipeline_events():
    result = generate_workout("lower body", minutes=30, llm=fake_llm)
    events = [e.step for e in result.trace.events]
    assert "resolve_concepts" in events
    assert "safety_filter" in events
    assert "compose_plan" in events
    assert all(e.ms >= 0 for e in result.trace.events)
