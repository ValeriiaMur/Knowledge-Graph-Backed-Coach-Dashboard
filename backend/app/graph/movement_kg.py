"""KG 1 — Movement/Clinical domain graph (in-process NetworkX MultiDiGraph).

Node kinds: exercise, muscle, joint, substructure, equipment, movement_pattern, condition.
Edge rels:  targets, stresses, requires, follows, part_of, located_in, contraindicated_for.
Safety decisions (phase 3) traverse these edges deterministically — never the LLM.
"""

from functools import lru_cache

import networkx as nx

from app.data_loader import load_exercises
from app.graph.ontology import ANATOMY_SUBSTRUCTURES, CONDITIONS, JOINT_MAPPINGS
from app.graph.terms import Kind, Rel


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
        g.add_node(node_id(Kind.MUSCLE, name), kind=Kind.MUSCLE, name=name)
    for name in joints:
        g.add_node(
            node_id(Kind.JOINT, name),
            kind=Kind.JOINT,
            name=name,
            skos_mappings=JOINT_MAPPINGS.get(name, []),
        )
    for name in equipment:
        g.add_node(node_id(Kind.EQUIPMENT, name), kind=Kind.EQUIPMENT, name=name)
    for name in patterns:
        g.add_node(node_id(Kind.MOVEMENT_PATTERN, name), kind=Kind.MOVEMENT_PATTERN, name=name)

    # Anatomy hierarchy: substructure -part_of-> joint.
    for joint, subs in ANATOMY_SUBSTRUCTURES.items():
        jid = node_id(Kind.JOINT, joint)
        if not g.has_node(jid):
            continue
        for sub in subs:
            sid = node_id(Kind.SUBSTRUCTURE, sub)
            g.add_node(sid, kind=Kind.SUBSTRUCTURE, name=sub)
            g.add_edge(sid, jid, rel=Rel.PART_OF)

    # Conditions: located_in structures, contraindicated_for movement patterns.
    for cond, spec in CONDITIONS.items():
        cid = node_id(Kind.CONDITION, cond)
        g.add_node(cid, kind=Kind.CONDITION, name=cond, skos_mappings=spec["skos_mappings"])
        for structure in spec["located_in"]:
            g.add_edge(cid, node_id(Kind.SUBSTRUCTURE, structure), rel=Rel.LOCATED_IN)
        for pattern, mode in spec["contraindicated_patterns"].items():
            pid = node_id(Kind.MOVEMENT_PATTERN, pattern)
            if g.has_node(pid):
                g.add_edge(cid, pid, rel=Rel.CONTRAINDICATED_FOR, mode=mode)

    # Exercises and their typed edges.
    for e in exercises:
        eid = node_id(Kind.EXERCISE, e.id)
        g.add_node(
            eid,
            kind=Kind.EXERCISE,
            name=e.name,
            priority_tier=e.priority_tier,
            is_bilateral=e.is_bilateral,
            side=e.side,
        )
        for m in e.muscle_groups:
            g.add_edge(eid, node_id(Kind.MUSCLE, m), rel=Rel.TARGETS)
        for j in e.joints_loaded:
            g.add_edge(eid, node_id(Kind.JOINT, j), rel=Rel.STRESSES)
        for q in e.equipment_required:
            g.add_edge(eid, node_id(Kind.EQUIPMENT, q), rel=Rel.REQUIRES)
        for p in e.movement_patterns:
            g.add_edge(eid, node_id(Kind.MOVEMENT_PATTERN, p), rel=Rel.FOLLOWS)

    return g


def descendants_of(g: nx.MultiDiGraph, node: str) -> set[str]:
    """All structures that are part_of `node`, transitively (part_of edges only)."""
    found: set[str] = set()
    frontier = [node]
    while frontier:
        current = frontier.pop()
        for src, _, data in g.in_edges(current, data=True):
            if data["rel"] == Rel.PART_OF and src not in found:
                found.add(src)
                frontier.append(src)
    return found


def exercises_loading(g: nx.MultiDiGraph, anatomy_node: str) -> set[str]:
    """Exercises stressing `anatomy_node` or any of its part_of descendants."""
    region = {anatomy_node} | descendants_of(g, anatomy_node)
    hits: set[str] = set()
    for target in region:
        for src, _, data in g.in_edges(target, data=True):
            if data["rel"] == Rel.STRESSES and g.nodes[src]["kind"] == Kind.EXERCISE:
                hits.add(src)
    return hits
