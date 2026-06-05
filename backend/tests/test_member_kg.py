"""Phase 2 (red-green): KG 2 — member context graph."""

from app.graph.member_kg import build_member_graph
from app.graph.movement_kg import node_id


def graph():
    return build_member_graph()


def test_member_node_exists():
    g = graph()
    members = [n for n, d in g.nodes(data=True) if d["kind"] == "member"]
    assert len(members) == 1
    assert g.nodes[members[0]]["name"] == "Jordan Rivera"


def test_injury_links_to_kg1_joint_concept():
    """KG 2 injuries anchor onto KG 1 canonical joints — the graphs relate."""
    g = graph()
    injuries = [n for n, d in g.nodes(data=True) if d["kind"] == "injury"]
    assert len(injuries) == 1
    targets = {v for _, v, d in g.out_edges(injuries[0], data=True) if d["rel"] == "affects"}
    assert node_id("joint", "knee") in targets
    assert g.nodes[injuries[0]]["side"] == "left"


def test_available_equipment_uses_kg1_equipment_ids():
    g = graph()
    member = next(n for n, d in g.nodes(data=True) if d["kind"] == "member")
    avail = {v for _, v, d in g.out_edges(member, data=True) if d["rel"] == "has_equipment"}
    assert node_id("equipment", "Dumbbell") in avail
    assert node_id("equipment", "Kettlebell") in avail
    assert node_id("equipment", "Barbell") not in avail


def test_workouts_chats_goals_ingested():
    g = graph()
    kinds = {}
    for _, d in g.nodes(data=True):
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    assert kinds.get("workout_session", 0) == 4
    assert kinds.get("chat_message", 0) == 4
    assert kinds.get("goal", 0) >= 2


def test_member_carries_timeseries_for_charts():
    """Adherence/biomarkers stay as attributes — chart endpoints read them directly."""
    g = graph()
    member = next(n for n, d in g.nodes(data=True) if d["kind"] == "member")
    adherence = g.nodes[member]["adherence"]
    assert adherence["trend"] == "declining"
    assert len(adherence["weekly_completion_pct"]) == 4
    assert "resting_hr_bpm" in g.nodes[member]["biomarkers"]
