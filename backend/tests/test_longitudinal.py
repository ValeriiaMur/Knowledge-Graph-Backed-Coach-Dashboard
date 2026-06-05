"""Red-green: longitudinal reasoning — trends over time, exposed as a copilot
tool and injected into the generator's composition payload."""

from app.copilot.longitudinal import compute_progression, linear_slope
from app.copilot.retrieval import TOOL_REGISTRY
from app.runtime.generator import generate_workout

ADHERENCE = [
    {"week_of": "2026-05-12", "pct": 100},
    {"week_of": "2026-05-19", "pct": 100},
    {"week_of": "2026-05-26", "pct": 75},
    {"week_of": "2026-06-02", "pct": 50},
]
WORKOUTS = [
    {"date": "2026-05-27", "completed": True, "duration_min": 26, "rpe": 6, "planned": True},
    {"date": "2026-05-29", "completed": False, "duration_min": 0, "rpe": None, "planned": True},
    {"date": "2026-06-01", "completed": True, "duration_min": 31, "rpe": 7, "planned": True},
    {"date": "2026-06-03", "completed": True, "duration_min": 28, "rpe": 6, "planned": True},
]
BIOMARKERS = {
    "sleep_hours_last_7_days": [6.1, 5.4, 7.2, 6.0, 5.1, 7.8, 6.3],
    "weight_trend_kg": [
        {"date": "2026-05-05", "kg": 72.4},
        {"date": "2026-05-19", "kg": 71.9},
        {"date": "2026-06-02", "kg": 71.2},
    ],
    "hrv_ms": 47,
    "resting_hr_bpm": 58,
}


def test_linear_slope_directions():
    assert linear_slope([1, 2, 3]) > 0
    assert linear_slope([3, 2, 1]) < 0
    assert linear_slope([2, 2, 2]) == 0
    assert linear_slope([5]) == 0  # degenerate: no trend from one point


def test_progression_detects_declining_adherence():
    p = compute_progression(ADHERENCE, WORKOUTS, BIOMARKERS)
    assert p["adherence"]["direction"] == "declining"
    assert p["adherence"]["latest_pct"] == 50
    assert p["adherence"]["delta_vs_prev"] == -25


def test_progression_volume_and_rpe():
    p = compute_progression(ADHERENCE, WORKOUTS, BIOMARKERS)
    assert p["volume"]["completed_sessions"] == 3
    assert p["volume"]["total_minutes"] == 85
    assert p["completion"]["planned"] == 4
    assert p["completion"]["completed"] == 3
    assert p["rpe"]["values"] == [6, 7, 6]


def test_progression_weight_and_summary():
    p = compute_progression(ADHERENCE, WORKOUTS, BIOMARKERS)
    assert round(p["weight"]["delta_kg"], 1) == -1.2
    assert "declining" in p["summary"]


def test_get_progression_is_a_registered_tool():
    fn = TOOL_REGISTRY["get_progression"]
    out = fn()
    assert out["adherence"]["direction"] == "declining"  # real member data
    assert "summary" in out


def test_generator_payload_carries_progression():
    seen: dict = {}

    def capture_llm(payload: dict) -> dict:
        seen.update(payload)
        ids = [c["node_id"] for c in payload["candidates"]]
        item = {"sets": 3, "reps": 10, "rest_sec": 60}
        return {
            "warmup": [{"exercise": ids[0], **item}],
            "main": [{"exercise": ids[1], **item}],
            "cooldown": [{"exercise": ids[2], **item}],
        }

    generate_workout("easy lower body", 30, llm=capture_llm, use_member_context=True)
    assert "member_progression" in seen
    assert seen["member_progression"]["adherence"]["direction"] == "declining"

    seen.clear()
    generate_workout("easy lower body", 30, llm=capture_llm, use_member_context=False)
    assert "member_progression" not in seen
