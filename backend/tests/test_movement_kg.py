"""Phase 2 (red-green): KG 1 — movement/clinical graph.

The graph must do real work: anatomy hierarchy for injury expansion,
typed edges for traversal, SKOS-style ontology mappings on nodes.
"""

from app.graph.movement_kg import (
    build_movement_graph,
    descendants_of,
    exercises_loading,
    node_id,
)


def graph():
    return build_movement_graph()


def test_all_catalog_concepts_become_nodes():
    g = graph()
    kinds = {}
    for _, data in g.nodes(data=True):
        kinds[data["kind"]] = kinds.get(data["kind"], 0) + 1
    assert kinds["exercise"] == 50
    assert kinds["muscle"] == 19
    assert kinds["joint"] == 9
    assert kinds["equipment"] == 32
    assert kinds["movement_pattern"] == 36


def test_typed_edges_exist():
    g = graph()
    rels = {d["rel"] for _, _, d in g.edges(data=True)}
    assert {"targets", "stresses", "requires", "follows", "part_of", "contraindicated_for"} <= rels


def test_anatomy_hierarchy_knee_has_substructures():
    """'knee' must cover sub-structures via part-of (spec scenario 2)."""
    subs = descendants_of(graph(), node_id("joint", "knee"))
    assert node_id("substructure", "patellofemoral joint") in subs
    assert node_id("substructure", "patella") in subs


def test_exercises_loading_knee_found_via_hierarchy():
    g = graph()
    hits = exercises_loading(g, node_id("joint", "knee"))
    assert len(hits) > 0
    # every hit must actually stress the knee per source data
    for ex_node in hits:
        joints = {v for _, v, d in g.out_edges(ex_node, data=True) if d["rel"] == "stresses"}
        assert node_id("joint", "knee") in joints


def test_patellofemoral_condition_contraindicates_plyometrics():
    """Injury notes: 'avoid deep knee flexion under load and plyometrics'."""
    g = graph()
    cond = node_id("condition", "patellofemoral pain syndrome")
    assert g.has_node(cond)
    contra = {v for _, v, d in g.out_edges(cond, data=True) if d["rel"] == "contraindicated_for"}
    assert node_id("movement_pattern", "cardio - plyometric") in contra


def test_knee_node_carries_snomed_mapping():
    g = graph()
    mappings = g.nodes[node_id("joint", "knee")].get("skos_mappings", [])
    assert any(m["scheme"] == "snomedct" and m["code"] == "49076000" for m in mappings)
