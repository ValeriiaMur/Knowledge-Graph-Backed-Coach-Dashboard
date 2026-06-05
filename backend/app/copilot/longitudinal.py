"""Longitudinal reasoning (spec nice-to-have): progression and adherence over
time, computed deterministically from member history. Exposed two ways:
as the `get_progression` copilot tool, and injected into the generator's
composition payload so plans respect the member's recent trajectory."""

from typing import Any


def linear_slope(values: list[float]) -> float:
    """Least-squares slope over the index (per-step change). 0 for <2 points."""
    n = len(values)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    denom = sum((i - mean_x) ** 2 for i in range(n))
    if denom == 0:
        return 0.0
    return sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values)) / denom


def _direction(slope: float, eps: float = 0.1) -> str:
    if slope > eps:
        return "improving"
    if slope < -eps:
        return "declining"
    return "flat"


def compute_progression(
    adherence_weeks: list[dict],
    workouts: list[dict],
    biomarkers: dict,
) -> dict[str, Any]:
    """Pure trend computation — no I/O, fully unit-testable."""
    pcts = [w["pct"] for w in adherence_weeks]
    adh_slope = linear_slope([float(p) for p in pcts])
    latest = pcts[-1] if pcts else None
    prev = pcts[-2] if len(pcts) > 1 else None

    done = sorted((w for w in workouts if w.get("completed")), key=lambda w: w["date"])
    planned = [w for w in workouts if w.get("planned")]
    minutes = [int(w.get("duration_min") or 0) for w in done]
    rpes = [w["rpe"] for w in done if w.get("rpe") is not None]

    weights = biomarkers.get("weight_trend_kg") or []
    weight_delta = float(weights[-1]["kg"]) - float(weights[0]["kg"]) if len(weights) > 1 else 0.0
    sleep = biomarkers.get("sleep_hours_last_7_days") or []
    sleep_avg = round(sum(sleep) / len(sleep), 1) if sleep else None

    adh_dir = _direction(adh_slope, eps=1.0)
    rpe_dir = _direction(linear_slope([float(r) for r in rpes]))
    delta_txt = (
        f", {latest - prev:+d} vs prior week" if prev is not None and latest is not None else ""
    )
    summary = (
        f"Adherence {adh_dir} ({latest}% latest{delta_txt}); "
        f"{len(done)}/{len(planned)} planned sessions completed, {sum(minutes)} min total; "
        f"RPE {rpe_dir} (avg {round(sum(rpes) / len(rpes), 1) if rpes else 'n/a'}); "
        f"weight {weight_delta:+.1f} kg across trend; sleep avg {sleep_avg} h."
    )

    return {
        "adherence": {
            "weekly_pct": pcts,
            "latest_pct": latest,
            "delta_vs_prev": (latest - prev) if (latest is not None and prev is not None) else None,
            "slope_pct_per_week": round(adh_slope, 2),
            "direction": adh_dir,
        },
        "volume": {
            "completed_sessions": len(done),
            "total_minutes": sum(minutes),
            "minutes_per_session": minutes,
        },
        "completion": {"planned": len(planned), "completed": len(done)},
        "rpe": {"values": rpes, "direction": rpe_dir},
        "weight": {"delta_kg": round(weight_delta, 2), "points": len(weights)},
        "sleep": {"avg_hours_last_7_days": sleep_avg},
        "summary": summary,
    }
