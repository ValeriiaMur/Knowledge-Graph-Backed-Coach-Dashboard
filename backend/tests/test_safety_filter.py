"""Phase 3 (red-green): safety filter — pure graph traversal, no LLM.
Covers the spec's three scenarios plus provenance of every removal."""

from app.data_loader import load_exercises
from app.graph.movement_kg import build_movement_graph, node_id
from app.safety.filter import SafetyConstraints, apply_safety_filter


def all_exercise_ids() -> set[str]:
    return {node_id("exercise", e.id) for e in load_exercises()}


# --- scenario 2: "her left knee is bothering her" ---------------------------


def test_injured_knee_excludes_knee_loading_exercises():
    result = apply_safety_filter(SafetyConstraints(injured_joints=["joint:knee"]))
    g = build_movement_graph()
    for ex in result.allowed:
        stressed = {v for _, v, d in g.out_edges(ex.node_id, data=True) if d["rel"] == "stresses"}
        assert node_id("joint", "knee") not in stressed


def test_injury_filter_records_provenance():
    result = apply_safety_filter(SafetyConstraints(injured_joints=["joint:knee"]))
    assert len(result.removed) > 0
    knee_removals = [r for r in result.removed if r.reason == "injury"]
    assert knee_removals
    # every removal names the graph path that justified it
    assert all("joint:knee" in r.graph_path for r in knee_removals)


def test_condition_down_ranks_but_keeps_exercises():
    """PFPS down-ranks deep-flexion patterns (not excluded — coach decides)."""
    result = apply_safety_filter(
        SafetyConstraints(conditions=["condition:patellofemoral pain syndrome"])
    )
    down_ranked = [e for e in result.allowed if e.down_ranked]
    assert down_ranked
    assert all(e.down_rank_reason for e in down_ranked)


# --- scenario 3: "no barbell, only dumbbells and a kettlebell" ---------------


def test_equipment_filter_drops_barbell_only_exercises():
    available = ["equipment:Dumbbell", "equipment:Kettlebell", "equipment:Yoga Mat"]
    result = apply_safety_filter(SafetyConstraints(available_equipment=available))
    g = build_movement_graph()
    for ex in result.allowed:
        required = {v for _, v, d in g.out_edges(ex.node_id, data=True) if d["rel"] == "requires"}
        assert required <= set(available)


def test_equipment_filter_suggests_substitutes():
    """A dropped barbell exercise should point at allowed alternatives sharing
    muscle + movement pattern (spec: 'find equivalent alternatives')."""
    available = ["equipment:Dumbbell", "equipment:Kettlebell", "equipment:Yoga Mat"]
    result = apply_safety_filter(SafetyConstraints(available_equipment=available))
    equip_removals = [r for r in result.removed if r.reason == "equipment"]
    assert equip_removals
    assert any(r.substitutes for r in equip_removals)


# --- scenario 1: "exclude deadlifts" -----------------------------------------


def test_explicit_exclusion_removes_all_name_variations():
    result = apply_safety_filter(SafetyConstraints(excluded_terms=["deadlift"]))
    assert all("deadlift" not in e.name.lower() for e in result.allowed)
    excl = [r for r in result.removed if r.reason == "explicit_exclusion"]
    assert all("deadlift" in r.name.lower() for r in excl)


# --- composition --------------------------------------------------------------


def test_combined_constraints_compose():
    result = apply_safety_filter(
        SafetyConstraints(
            injured_joints=["joint:knee"],
            available_equipment=["equipment:Dumbbell", "equipment:Yoga Mat"],
            excluded_terms=["deadlift"],
        )
    )
    assert result.allowed  # the pool must not collapse for the seeded member
    assert len(result.allowed) + len(result.removed) == 50


def test_empty_constraints_allow_everything():
    result = apply_safety_filter(SafetyConstraints())
    assert len(result.allowed) == 50
    assert not result.removed
