"""KG 2 — Member Context graph. Anchors onto KG 1 canonical concepts
(joints via injury `affects`, equipment via `has_equipment`) so the two graphs relate.
Timeseries (adherence, biomarkers, labs) stay as member-node attributes — the
chart endpoints (phase 5) read them directly; graph nodes are for relationships.
"""

from functools import lru_cache

import networkx as nx

from app.data_loader import load_member_context
from app.graph.movement_kg import node_id
from app.graph.ontology import REGION_ALIASES
from app.graph.terms import Kind, Rel


def member_node(g: nx.MultiDiGraph) -> str:
    """Node id of the single member node — the anchor KG 2 consumers traverse from."""
    return next(n for n, d in g.nodes(data=True) if d["kind"] == Kind.MEMBER)


def _ensure_ref(g: nx.MultiDiGraph, kind: str, name: str) -> None:
    """Reference node mirroring a KG 1 canonical concept (same node id in both graphs)."""
    nid = node_id(kind, name)
    if not g.has_node(nid):
        g.add_node(nid, kind=kind, name=name, ref="movement_kg")


@lru_cache(maxsize=1)
def build_member_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    m = load_member_context()
    profile = m.profile

    mid = node_id(Kind.MEMBER, profile["id"])
    g.add_node(
        mid,
        kind=Kind.MEMBER,
        name=profile["name"],
        profile=profile,
        preferences=m.preferences,
        adherence=m.adherence,
        biomarkers=m.biomarkers,
        labs=m.labs,
        coach_brief=m.coach_brief,
    )

    for inj in m.injuries:
        iid = node_id(Kind.INJURY, inj["id"])
        region = inj.get("region", "")
        side = region.split()[0] if region.startswith(("left", "right")) else None
        g.add_node(
            iid,
            kind=Kind.INJURY,
            name=region,
            side=side,
            status=inj.get("status"),
            severity=inj.get("severity"),
            since=inj.get("since"),
            notes=inj.get("notes"),
        )
        g.add_edge(mid, iid, rel=Rel.HAS_INJURY)
        joint = inj.get("joint") or REGION_ALIASES.get(region, region)
        _ensure_ref(g, Kind.JOINT, joint)
        g.add_edge(iid, node_id(Kind.JOINT, joint), rel=Rel.AFFECTS)

    for eq in m.equipment_available:
        _ensure_ref(g, Kind.EQUIPMENT, eq)
        g.add_edge(mid, node_id(Kind.EQUIPMENT, eq), rel=Rel.HAS_EQUIPMENT)

    for goal in m.goals:
        gid = node_id(Kind.GOAL, goal["id"])
        g.add_node(
            gid,
            kind=Kind.GOAL,
            name=goal["text"],
            **{k: v for k, v in goal.items() if k not in {"id", "text"}},
        )
        g.add_edge(mid, gid, rel=Rel.HAS_GOAL)

    for i, session in enumerate(m.workout_history):
        sid = node_id(Kind.WORKOUT_SESSION, f"{session['date']}_{i}")
        g.add_node(sid, kind=Kind.WORKOUT_SESSION, name=session.get("title", ""), **session)
        g.add_edge(mid, sid, rel=Rel.PERFORMED)

    for i, msg in enumerate(m.chat_history):
        cid = node_id(Kind.CHAT_MESSAGE, f"{msg['ts']}_{i}")
        g.add_node(cid, kind=Kind.CHAT_MESSAGE, name=msg.get("text", "")[:60], **msg)
        g.add_edge(mid, cid, rel=Rel.CHATTED)

    return g
