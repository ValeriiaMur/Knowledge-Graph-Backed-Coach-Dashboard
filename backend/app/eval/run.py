"""Eval pipeline (`make eval`) — resolver accuracy + safety-filter correctness
over a hand-labeled set. Doubles as the regression suite (PRESEARCH §9/§13)."""

from app.resolver.resolver import resolve
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
        r = resolve(query)
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
                v == case["must_not_stress"] for _, v, d in edges if d["rel"] == "stresses"
            ):
                violations.append(ex.name)
            if case.get("must_not_require") and any(
                v == case["must_not_require"] for _, v, d in edges if d["rel"] == "requires"
            ):
                violations.append(ex.name)
            if case.get("must_not_name") and case["must_not_name"] in ex.name.lower():
                violations.append(ex.name)
        if violations:
            failures.append(f"  safety [{case['name']}]: violations {violations}")
        else:
            passed += 1
    return passed, len(SAFETY_SCENARIOS), failures


def main() -> int:
    r_ok, r_total, r_fail = run_resolver_eval()
    s_ok, s_total, s_fail = run_safety_eval()
    print(f"resolver accuracy: {r_ok}/{r_total} ({r_ok / r_total:.0%})")
    print(f"safety scenarios:  {s_ok}/{s_total}")
    for line in r_fail + s_fail:
        print(line)
    return 0 if not (r_fail or s_fail) else 1


if __name__ == "__main__":
    raise SystemExit(main())
