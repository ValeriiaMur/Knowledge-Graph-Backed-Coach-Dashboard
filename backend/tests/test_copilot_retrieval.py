"""Phase 5 (red-green): copilot retrieval — every answer grounded in KG 2."""

from app.copilot.retrieval import (
    TOOL_REGISTRY,
    get_adherence,
    get_brief,
    get_churn_risk,
    get_timeseries,
    what_changed,
)


def test_brief_surfaces_morning_tasks():
    brief = get_brief()
    assert brief["generated_for"] == "2026-06-04"
    types = {t["type"] for t in brief["morning_tasks"]}
    assert {"celebrate", "review_risk"} <= types


def test_adherence_is_grounded_series():
    a = get_adherence()
    assert a["trend"] == "declining"
    assert [w["pct"] for w in a["weeks"]] == [100, 100, 75, 50]


def test_churn_risk_with_reasons():
    risk = get_churn_risk()
    assert risk["level"] == "elevated"
    assert len(risk["reasons"]) >= 2


def test_what_changed_compares_last_two_weeks():
    delta = what_changed()
    assert delta["adherence"]["previous_pct"] == 75
    assert delta["adherence"]["current_pct"] == 50
    assert delta["adherence"]["delta_pct"] == -25


def test_timeseries_for_charts():
    sleep = get_timeseries("sleep")
    assert sleep["metric"] == "sleep"
    assert len(sleep["points"]) == 7
    adherence = get_timeseries("adherence")
    assert len(adherence["points"]) == 4


def test_unknown_metric_is_honest():
    out = get_timeseries("blood_pressure")
    assert out["error"]  # "not in this member's context" beats a guess


def test_registry_exposes_all_tools():
    expected = {
        "get_brief",
        "get_adherence",
        "get_churn_risk",
        "get_sleep",
        "get_biomarkers",
        "get_labs",
        "get_injuries",
        "get_goals",
        "get_preferences",
        "get_chat_history",
        "get_workout_history",
        "what_changed",
        "get_timeseries",
    }
    assert expected <= set(TOOL_REGISTRY)
    for fn in TOOL_REGISTRY.values():
        assert callable(fn)
