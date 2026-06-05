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

    mid = node_id("member", profile["id"])
    g.add_node(
        mid,
        kind="member",
        name=profile["name"],
        profile=profile,
        preferences=m.preferences,
        adherence=m.adherence,
        biomarkers=m.biomarkers,
        labs=m.labs,
        coach_brief=m.coach_brief,
    )

    for inj in m.injuries:
        iid = node_id("injury", inj["id"])
        region = inj.get("region", "")
        side = region.split()[0] if region.startswith(("left", "right")) else None
        g.add_node(
            iid,
            kind="injury",
            name=region,
            side=side,
            status=inj.get("status"),
            severity=inj.get("severity"),
            since=inj.get("since"),
            notes=inj.get("notes"),
        )
        g.add_edge(mid, iid, rel="has_injury")
        joint = inj.get("joint") or REGION_ALIASES.get(region, region)
        _ensure_ref(g, "joint", joint)
        g.add_edge(iid, node_id("joint", joint), rel="affects")

    for eq in m.equipment_available:
        _ensure_ref(g, "equipment", eq)
        g.add_edge(mid, node_id("equipment", eq), rel="has_equipment")

    for goal in m.goals:
        gid = node_id("goal", goal["id"])
        g.add_node(
            gid,
            kind="goal",
            name=goal["text"],
            **{k: v for k, v in goal.items() if k not in {"id", "text"}},
        )
        g.add_edge(mid, gid, rel="has_goal")

    for i, session in enumerate(m.workout_history):
        sid = node_id("workout_session", f"{session['date']}_{i}")
        g.add_node(sid, kind="workout_session", name=session.get("title", ""), **session)
        g.add_edge(mid, sid, rel="performed")

    for i, msg in enumerate(m.chat_history):
        cid = node_id("chat_message", f"{msg['ts']}_{i}")
        g.add_node(cid, kind="chat_message", name=msg.get("text", "")[:60], **msg)
        g.add_edge(mid, cid, rel="chatted")

    return g
