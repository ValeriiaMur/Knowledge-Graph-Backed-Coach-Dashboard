"""Copilot retrieval tools — every function reads KG 2 (or its member-node attrs).
The LLM never answers member questions from memory; it calls these.
Unknown data → explicit error: 'not in this member's context' beats a guess."""

from typing import Any

from app.graph.member_kg import build_member_graph


def _member() -> tuple[Any, dict]:
    g = build_member_graph()
    nid = next(n for n, d in g.nodes(data=True) if d["kind"] == "member")
    return g, g.nodes[nid]


def get_brief() -> dict:
    _, m = _member()
    return m["coach_brief"]


def get_adherence() -> dict:
    _, m = _member()
    a = m["adherence"]
    return {"trend": a["trend"], "weeks": a["weekly_completion_pct"]}


def get_churn_risk() -> dict:
    _, m = _member()
    return m["coach_brief"]["churn_risk"]


def get_sleep() -> dict:
    _, m = _member()
    return {"sleep_hours_last_7_days": m["biomarkers"]["sleep_hours_last_7_days"]}


def get_biomarkers() -> dict:
    _, m = _member()
    return m["biomarkers"]


def get_labs() -> dict:
    _, m = _member()
    return m["labs"]


def get_preferences() -> dict:
    _, m = _member()
    return m["preferences"]


def get_injuries() -> list[dict]:
    g, _ = _member()
    return [
        {
            "region": d["name"],
            "side": d["side"],
            "status": d["status"],
            "severity": d["severity"],
            "since": d["since"],
            "notes": d["notes"],
        }
        for _, d in g.nodes(data=True)
        if d["kind"] == "injury"
    ]


def get_goals() -> list[dict]:
    g, _ = _member()
    return [
        {"text": d["name"], **{k: v for k, v in d.items() if k not in {"kind", "name"}}}
        for _, d in g.nodes(data=True)
        if d["kind"] == "goal"
    ]


def get_chat_history() -> list[dict]:
    g, _ = _member()
    msgs = [d for _, d in g.nodes(data=True) if d["kind"] == "chat_message"]
    return sorted(
        (
            {
                "ts": d["ts"],
                "from": d["from"],
                "text": d["text"],
                # spec: "chat with history/images" — attachments must survive
                **({"attachments": d["attachments"]} if d.get("attachments") else {}),
            }
            for d in msgs
        ),
        key=lambda x: x["ts"],
    )


def get_workout_history() -> list[dict]:
    g, _ = _member()
    sessions = [d for _, d in g.nodes(data=True) if d["kind"] == "workout_session"]
    keep = ("date", "title", "planned", "completed", "duration_min", "rpe", "exercises")
    return sorted(
        ({k: d.get(k) for k in keep} for d in sessions),
        key=lambda x: x["date"],
    )


def what_changed() -> dict:
    """Week-over-week deltas the morning brief cares about."""
    weeks = get_adherence()["weeks"]
    prev, cur = weeks[-2]["pct"], weeks[-1]["pct"]
    return {
        "adherence": {"previous_pct": prev, "current_pct": cur, "delta_pct": cur - prev},
        "trend": get_adherence()["trend"],
        "recent_workouts": get_workout_history()[-2:],
        "latest_chats": get_chat_history()[-2:],
    }


def get_progression() -> dict:
    """Longitudinal progression: adherence/RPE/volume/weight trends over time,
    with a one-line summary. Use for 'how is she progressing?' questions."""
    from app.copilot.longitudinal import compute_progression

    _, m = _member()
    return compute_progression(
        m["adherence"]["weekly_completion_pct"],
        get_workout_history(),
        m["biomarkers"],
    )


def get_timeseries(metric: str) -> dict:
    """Chart-ready series. Supported: adherence, sleep, resting_hr, hrv, weight."""
    _, m = _member()
    bio = m["biomarkers"]
    if metric == "adherence":
        pts = [{"x": w["week_of"], "y": w["pct"]} for w in m["adherence"]["weekly_completion_pct"]]
        return {"metric": metric, "unit": "%", "points": pts}
    if metric == "sleep":
        pts = [{"x": f"day {i + 1}", "y": v} for i, v in enumerate(bio["sleep_hours_last_7_days"])]
        return {"metric": metric, "unit": "hours", "points": pts}
    series_keys = {"resting_hr": "resting_hr_bpm", "hrv": "hrv_ms", "weight": "weight_trend_kg"}
    if metric in series_keys:
        raw = bio[series_keys[metric]]
        pts = (
            [{"x": p.get("date", str(i)), "y": p.get("value", p)} for i, p in enumerate(raw)]
            if isinstance(raw, list)
            else [{"x": "current", "y": raw}]
        )
        return {"metric": metric, "unit": series_keys[metric], "points": pts}
    return {
        "metric": metric,
        "points": [],
        "error": f"'{metric}' is not in this member's context",
    }


TOOL_REGISTRY: dict[str, Any] = {
    "get_brief": get_brief,
    "get_adherence": get_adherence,
    "get_churn_risk": get_churn_risk,
    "get_sleep": get_sleep,
    "get_biomarkers": get_biomarkers,
    "get_labs": get_labs,
    "get_injuries": get_injuries,
    "get_goals": get_goals,
    "get_preferences": get_preferences,
    "get_chat_history": get_chat_history,
    "get_workout_history": get_workout_history,
    "what_changed": what_changed,
    "get_progression": get_progression,
    "get_timeseries": get_timeseries,
}
