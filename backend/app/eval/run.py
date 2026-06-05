"""Eval pipeline (`make eval`) — resolver accuracy + safety-filter correctness
over a hand-labeled set. Doubles as the regression suite (PRESEARCH §9/§13)."""

from app.graph.terms import Rel
from app.resolver.resolver import resolve_concept
from app.safety.filter import SafetyConstraints, apply_safety_filter

# query -> expected node_id (None = must honestly no-match)
RESOLVER_CASES: dict[str, str | None] = {
    "knee": "joint:knee",
    "left knee": "joint:knee",
    "pecs": "muscle:chest",
    "abs": "muscle:core",
    "kettlebell": "equipment:Kettlebell",
    "ketlebell": "equipment:Kettlebell",
    "dumbbells": "equipment:Dumbbell",
    "lower back": "joint:lumbar spine",
    "bad lower back": "joint:lumbar spine",
    "shoulders": "muscle:deltoids",
    "quadriceps": "muscle:quads",
    "hamstrings": "muscle:hamstrings",
    "stability bal": "equipment:Stability Ball",
    "flibbertigibbet": None,
    "zzqxv": None,
}

SAFETY_SCENARIOS = [
    {
        "name": "left knee injury",
        "constraints": SafetyConstraints(injured_joints=["joint:knee"]),
        "must_not_stress": "joint:knee",
    },
    {
        "name": "no barbell",
        "constraints": SafetyConstraints(
            available_equipment=[
                "equipment:Dumbbell",
                "equipment:Kettlebell",
                "equipment:Yoga Mat",
                "equipment:Resistance Band - Loop",
                "equipment:Flat Bench",
            ]
        ),
        "must_not_require": "equipment:Barbell",
    },
    {
        "name": "exclude deadlifts",
        "constraints": SafetyConstraints(excluded_terms=["deadlift"]),
        "must_not_name": "deadlift",
    },
]


def run_resolver_eval() -> tuple[int, int, list[str]]:
    correct, failures = 0, []
    for query, expected in RESOLVER_CASES.items():
        # Deliberate single-concept lookups → use the full 3-pass resolver,
        # including the Voyage embedding pass when a key is present.
        r = resolve_concept(query)
        got = r.node_id
        if got == expected:
            correct += 1
        else:
            failures.append(f"  resolver: {query!r} -> {got} (expected {expected}, {r.method})")
    return correct, len(RESOLVER_CASES), failures


def run_safety_eval() -> tuple[int, int, list[str]]:
    from app.graph.movement_kg import build_movement_graph

    g = build_movement_graph()
    passed, failures = 0, []
    for case in SAFETY_SCENARIOS:
        result = apply_safety_filter(case["constraints"])
        violations = []
        for ex in result.allowed:
            edges = list(g.out_edges(ex.node_id, data=True))
            if case.get("must_not_stress") and any(
                v == case["must_not_stress"] for _, v, d in edges if d["rel"] == Rel.STRESSES
            ):
                violations.append(ex.name)
            if case.get("must_not_require") and any(
                v == case["must_not_require"] for _, v, d in edges if d["rel"] == Rel.REQUIRES
            ):
                violations.append(ex.name)
            if case.get("must_not_name") and case["must_not_name"] in ex.name.lower():
                violations.append(ex.name)
        if violations:
            failures.append(f"  safety [{case['name']}]: violations {violations}")
        else:
            passed += 1
    return passed, len(SAFETY_SCENARIOS), failures


# Recommendation-quality scenarios (nice-to-have eval, ASSESSMENT "What we're
# evaluating"): structural plan checks with the deterministic offline composer,
# so the gate runs in CI without an API key. The LLM only reorders within
# already-approved candidates, so structure/safety properties hold identically.
PLAN_SCENARIOS = [
    ("Full-body strength, exclude deadlifts", 30),
    ("Lower-body session, her left knee is bothering her", 30),
    ("Upper-body push, no barbell, only dumbbells and kettlebell", 45),
]


def _offline_compose(payload: dict) -> dict:
    ids = [c["node_id"] for c in payload["candidates"]]
    item = {"sets": 3, "reps": 10, "rest_sec": 60}
    last = min(5, len(ids) - 1)
    return {
        "warmup": [{"exercise": ids[0], **item}],
        "main": [{"exercise": i, **item} for i in ids[1:last]],
        "cooldown": [{"exercise": ids[last], **item}],
    }


def run_plan_quality_eval() -> tuple[int, int, list[str]]:
    from app.runtime.generator import generate_workout

    passed, failures = 0, []
    for prompt, minutes in PLAN_SCENARIOS:
        result = generate_workout(prompt, minutes, llm=_offline_compose, use_member_context=True)
        problems = []
        if result.error or result.plan is None:
            problems.append(f"generation error: {result.error}")
        else:
            plan = result.plan
            if not (plan.warmup and plan.main and plan.cooldown):
                problems.append("missing warmup/main/cooldown section")
            removed_ids = {r.node_id for r in result.provenance.removed}
            items = plan.warmup + plan.main + plan.cooldown
            if any(i.exercise in removed_ids for i in items):
                problems.append("plan contains a safety-filtered exercise")
            if any(i.sets < 1 or i.rest_sec < 0 for i in items):
                problems.append("nonsensical dose (sets < 1 or negative rest)")
            if not result.provenance.removed and not result.provenance.resolved_concepts:
                problems.append("empty provenance — trace requirement violated")
        if problems:
            failures.append(f"  plan [{prompt[:40]}…]: {problems}")
        else:
            passed += 1
    return passed, len(PLAN_SCENARIOS), failures


def main() -> int:
    r_ok, r_total, r_fail = run_resolver_eval()
    s_ok, s_total, s_fail = run_safety_eval()
    p_ok, p_total, p_fail = run_plan_quality_eval()
    print(f"resolver accuracy: {r_ok}/{r_total} ({r_ok / r_total:.0%})")
    print(f"safety scenarios:  {s_ok}/{s_total}")
    print(f"plan quality:      {p_ok}/{p_total}")
    for line in r_fail + s_fail + p_fail:
        print(line)
    return 0 if not (r_fail or s_fail or p_fail) else 1


if __name__ == "__main__":
    raise SystemExit(main())
