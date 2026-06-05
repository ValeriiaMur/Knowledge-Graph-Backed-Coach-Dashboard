"""Derive SafetyConstraints from (a) the member's KG 2 context and (b) the coach prompt.

Prompt scanning is deterministic n-gram resolution — safety-relevant constraints must
not depend on LLM extraction (PRESEARCH §3). The LLM only composes from the
pre-filtered pool. Trade-off documented for the README: an LLM extractor would
catch richer phrasings; safety correctness wins for the take-home.
"""

import re
from dataclasses import dataclass, field

from app.graph.member_kg import build_member_graph
from app.resolver.resolver import ResolvedConcept, resolve
from app.safety.filter import SafetyConstraints

EXCLUDE_RE = re.compile(r"\b(?:exclude|no|skip|without|drop)\s+([a-z][a-z \-]{2,30}?)s?\b")

STOPWORDS = {
    "a",
    "an",
    "the",
    "my",
    "her",
    "his",
    "their",
    "with",
    "and",
    "or",
    "for",
    "around",
    "today",
    "please",
    "some",
    "that",
    "this",
    "of",
    "on",
    "in",
    "is",
    "avoid",
    "aggravating",
    "exercises",
    "exercise",
    "workout",
    "body",
    "day",
    "full",
    "lower",
    "upper",
    "easy",
    "solid",
    "bothering",
}


@dataclass
class DerivedConstraints:
    constraints: SafetyConstraints
    resolved_concepts: list[ResolvedConcept] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)


def _ngrams(text: str, max_n: int = 3) -> list[str]:
    words = re.findall(r"[a-z\-]+", text.lower())
    grams = []
    for n in range(max_n, 0, -1):
        grams += [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    return grams


def derive_constraints(prompt: str, use_member_context: bool = True) -> DerivedConstraints:
    constraints = SafetyConstraints()
    resolved: list[ResolvedConcept] = []
    unresolved: list[str] = []

    # (a) Member context: injuries, conditions, equipment — applied automatically.
    if use_member_context:
        g = build_member_graph()
        member = next(n for n, d in g.nodes(data=True) if d["kind"] == "member")
        for _, inj, d in g.out_edges(member, data=True):
            if d["rel"] != "has_injury":
                continue
            for _, joint, dd in g.out_edges(inj, data=True):
                if dd["rel"] == "affects":
                    constraints.injured_joints.append(joint)
            # The seeded PFPS condition rides with the knee injury.
            notes = (g.nodes[inj].get("notes") or "").lower()
            if "patellofemoral" in notes:
                constraints.conditions.append("condition:patellofemoral pain syndrome")
        equipment = [v for _, v, d in g.out_edges(member, data=True) if d["rel"] == "has_equipment"]
        if equipment:
            constraints.available_equipment = equipment

    # (b) Prompt: explicit exclusions ("no deadlifts", "exclude lunges").
    for m in EXCLUDE_RE.finditer(prompt.lower()):
        constraints.excluded_terms.append(m.group(1).strip())

    # (c) Prompt: resolve concept mentions (longest n-gram first, no overlaps).
    consumed: set[str] = set(constraints.excluded_terms)
    for gram in _ngrams(prompt):
        if gram in STOPWORDS or gram in consumed or len(gram) < 3:
            continue
        if any(gram in c for c in consumed):
            continue
        r = resolve(gram)
        if r.method != "none":
            resolved.append(r)
            consumed.add(gram)
            if r.node_id and r.node_id.startswith("joint:"):
                constraints.injured_joints.append(r.node_id)

    # (d) Honest reporting: "avoid X" terms that resolved to nothing.
    for m in re.finditer(r"\bavoid\s+(?:the\s+)?([a-z\-]+)", prompt.lower()):
        term = m.group(1)
        if term not in consumed and resolve(term).method == "none":
            unresolved.append(term)

    # de-dup, stable order
    constraints.injured_joints = list(dict.fromkeys(constraints.injured_joints))
    constraints.conditions = list(dict.fromkeys(constraints.conditions))
    return DerivedConstraints(constraints, resolved, unresolved)
