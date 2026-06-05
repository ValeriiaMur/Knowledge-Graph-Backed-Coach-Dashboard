"""Safety filter — deterministic graph traversal over KG 1. No LLM anywhere.

Order of operations (each removal carries the graph path that justified it):
1. explicit exclusions (name match on coach's words)
2. injury: injured joint expanded via part_of⁻¹, drop exercises stressing the region
3. condition contraindications: mode=exclude drops, mode=down_rank flags
4. equipment: drop exercises requiring unavailable equipment; compute substitutes

The LLM (phase 4) only ever sees `allowed` — it cannot un-filter anything.
"""

from dataclasses import dataclass, field

import networkx as nx

from app.graph.movement_kg import build_movement_graph, descendants_of


@dataclass
class SafetyConstraints:
    injured_joints: list[str] = field(default_factory=list)  # KG node ids
    conditions: list[str] = field(default_factory=list)
    available_equipment: list[str] | None = None  # None = no equipment constraint
    excluded_terms: list[str] = field(default_factory=list)


@dataclass
class AllowedExercise:
    node_id: str
    name: str
    priority_tier: int
    down_ranked: bool = False
    down_rank_reason: str | None = None


@dataclass
class RemovedExercise:
    node_id: str
    name: str
    reason: str  # explicit_exclusion | injury | condition | equipment
    graph_path: str  # human-readable traversal that justified removal
    substitutes: list[str] = field(default_factory=list)  # allowed alternative names


@dataclass
class FilterResult:
    allowed: list[AllowedExercise]
    removed: list[RemovedExercise]


def _out(g: nx.MultiDiGraph, node: str, rel: str) -> set[str]:
    return {v for _, v, d in g.out_edges(node, data=True) if d["rel"] == rel}


def apply_safety_filter(constraints: SafetyConstraints) -> FilterResult:
    g = build_movement_graph()
    exercises = [n for n, d in g.nodes(data=True) if d["kind"] == "exercise"]

    removed: list[RemovedExercise] = []
    down_rank: dict[str, str] = {}
    surviving: list[str] = []

    # Condition expansion: patterns to exclude / down-rank.
    exclude_patterns: dict[str, str] = {}
    down_rank_patterns: dict[str, str] = {}
    for cond in constraints.conditions:
        if not g.has_node(cond):
            continue
        for _, pattern, d in g.out_edges(cond, data=True):
            if d["rel"] != "contraindicated_for":
                continue
            path = f"{cond} -contraindicated_for({d['mode']})-> {pattern}"
            if d["mode"] == "exclude":
                exclude_patterns[pattern] = path
            else:
                down_rank_patterns[pattern] = path

    # Injury expansion: joint + part_of descendants.
    injured_region: dict[str, str] = {}  # anatomy node -> source joint
    for joint in constraints.injured_joints:
        if not g.has_node(joint):
            continue
        injured_region[joint] = joint
        for sub in descendants_of(g, joint):
            injured_region[sub] = joint

    for ex in exercises:
        name = g.nodes[ex]["name"]

        # 1 · explicit exclusions
        term = next((t for t in constraints.excluded_terms if t.lower() in name.lower()), None)
        if term:
            removed.append(
                RemovedExercise(ex, name, "explicit_exclusion", f'coach said exclude "{term}"')
            )
            continue

        # 2 · injury traversal
        stressed = _out(g, ex, "stresses")
        hit = next((s for s in stressed if s in injured_region), None)
        if hit:
            src = injured_region[hit]
            removed.append(
                RemovedExercise(
                    ex,
                    name,
                    "injury",
                    f"{ex} -stresses-> {hit}"
                    + (f" -part_of-> {src}" if hit != src else f" (injured: {src})"),
                )
            )
            continue

        # 3 · condition contraindications
        patterns = _out(g, ex, "follows")
        excl_hit = next((p for p in patterns if p in exclude_patterns), None)
        if excl_hit:
            removed.append(
                RemovedExercise(
                    ex, name, "condition", f"{ex} -follows-> {exclude_patterns[excl_hit]}"
                )
            )
            continue
        dr_hit = next((p for p in patterns if p in down_rank_patterns), None)
        if dr_hit:
            down_rank[ex] = f"{ex} -follows-> {down_rank_patterns[dr_hit]}"

        # 4 · equipment availability
        if constraints.available_equipment is not None:
            required = _out(g, ex, "requires")
            missing = required - set(constraints.available_equipment)
            if missing:
                removed.append(
                    RemovedExercise(
                        ex,
                        name,
                        "equipment",
                        f"{ex} -requires-> {sorted(missing)} ∉ available",
                    )
                )
                continue

        surviving.append(ex)

    allowed = [
        AllowedExercise(
            node_id=ex,
            name=g.nodes[ex]["name"],
            priority_tier=g.nodes[ex]["priority_tier"],
            down_ranked=ex in down_rank,
            down_rank_reason=down_rank.get(ex),
        )
        for ex in surviving
    ]

    # Substitutes for equipment removals: allowed exercises sharing a muscle AND a pattern.
    allowed_ids = {a.node_id for a in allowed}
    for r in removed:
        if r.reason != "equipment":
            continue
        muscles = _out(g, r.node_id, "targets")
        patterns = _out(g, r.node_id, "follows")
        subs = [
            g.nodes[a]["name"]
            for a in allowed_ids
            if _out(g, a, "targets") & muscles and _out(g, a, "follows") & patterns
        ]
        r.substitutes = sorted(subs)[:3]

    return FilterResult(allowed=allowed, removed=removed)
