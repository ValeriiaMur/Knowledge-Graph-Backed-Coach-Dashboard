"""KG 1 — Movement/Clinical domain graph (in-process NetworkX MultiDiGraph).

Node kinds: exercise, muscle, joint, substructure, equipment, movement_pattern, condition.
Edge rels:  targets, stresses, requires, follows, part_of, located_in, contraindicated_for.
Safety decisions (phase 3) traverse these edges deterministically — never the LLM.
"""

from functools import lru_cache

import networkx as nx

from app.data_loader import load_exercises
from app.graph.ontology import ANATOMY_SUBSTRUCTURES, CONDITIONS, JOINT_MAPPINGS


def node_id(kind: str, name: str) -> str:
    return f"{kind}:{name}"


@lru_cache(maxsize=1)
def build_movement_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    exercises = load_exercises()

    # Canonical concept nodes derived from the catalog itself (guarantees coverage).
    muscles = sorted({m for e in exercises for m in e.muscle_groups})
    joints = sorted({j for e in exercises for j in e.joints_loaded})
    equipment = sorted({q for e in exercises for q in e.equipment_required})
    patterns = sorted({p for e in exercises for p in e.movement_patterns})

    for name in muscles:
        g.add_node(node_id("muscle", name), kind="muscle", name=name)
    for name in joints:
        g.add_node(
            node_id("joint", name),
            kind="joint",
            name=name,
            skos_mappings=JOINT_MAPPINGS.get(name, []),
        )
    for name in equipment:
        g.add_node(node_id("equipment", name), kind="equipment", name=name)
    for name in patterns:
        g.add_node(node_id("movement_pattern", name), kind="movement_pattern", name=name)

    # Anatomy hierarchy: substructure -part_of-> joint.
    for joint, subs in ANATOMY_SUBSTRUCTURES.items():
        jid = node_id("joint", joint)
        if not g.has_node(jid):
            continue
        for sub in subs:
            sid = node_id("substructure", sub)
            g.add_node(sid, kind="substructure", name=sub)
            g.add_edge(sid, jid, rel="part_of")

    # Conditions: located_in structures, contraindicated_for movement patterns.
    for cond, spec in CONDITIONS.items():
        cid = node_id("condition", cond)
        g.add_node(cid, kind="condition", name=cond, skos_mappings=spec["skos_mappings"])
        for structure in spec["located_in"]:
            g.add_edge(cid, node_id("substructure", structure), rel="located_in")
        for pattern, mode in spec["contraindicated_patterns"].items():
            pid = node_id("movement_pattern", pattern)
            if g.has_node(pid):
                g.add_edge(cid, pid, rel="contraindicated_for", mode=mode)

    # Exercises and their typed edges.
    for e in exercises:
        eid = node_id("exercise", e.id)
        g.add_node(
            eid,
            kind="exercise",
            name=e.name,
            priority_tier=e.priority_tier,
            is_bilateral=e.is_bilateral,
            side=e.side,
        )
        for m in e.muscle_groups:
            g.add_edge(eid, node_id("muscle", m), rel="targets")
        for j in e.joints_loaded:
            g.add_edge(eid, node_id("joint", j), rel="stresses")
        for q in e.equipment_required:
            g.add_edge(eid, node_id("equipment", q), rel="requires")
        for p in e.movement_patterns:
            g.add_edge(eid, node_id("movement_pattern", p), rel="follows")

    return g


def descendants_of(g: nx.MultiDiGraph, node: str) -> set[str]:
    """All structures that are part_of `node`, transitively (part_of edges only)."""
    found: set[str] = set()
    frontier = [node]
    while frontier:
        current = frontier.pop()
        for src, _, data in g.in_edges(current, data=True):
            if data["rel"] == "part_of" and src not in found:
                found.add(src)
                frontier.append(src)
    return found


def exercises_loading(g: nx.MultiDiGraph, anatomy_node: str) -> set[str]:
    """Exercises stressing `anatomy_node` or any of its part_of descendants."""
    region = {anatomy_node} | descendants_of(g, anatomy_node)
    hits: set[str] = set()
    for target in region:
        for src, _, data in g.in_edges(target, data=True):
            if data["rel"] == "stresses" and g.nodes[src]["kind"] == "exercise":
                hits.add(src)
    return hits
