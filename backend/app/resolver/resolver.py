"""3-pass concept resolver: exact → fuzzy → embedding, with explicit thresholds.

Free text ("knee", "pecs", "ketlebell") → canonical KG 1 node ids.
Pass 3 is injectable: production wires Voyage embeddings (app/resolver/embeddings.py);
tests inject a fake. Below-threshold = honest no-match, never a guess —
an unresolved safety constraint must surface to the coach, not vanish.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache

from rapidfuzz import fuzz, process

from app.graph.movement_kg import build_movement_graph
from app.graph.ontology import REGION_ALIASES
from app.graph.terms import Kind

FUZZY_FLOOR = 0.85  # rapidfuzz WRatio/100; tuned on the eval set (phase 6)
EMBEDDING_FLOOR = 0.75  # cosine similarity floor

# Curated synonyms count as exact matches (confidence 1.0): they're vetted, not guessed.
SYNONYMS: dict[str, str] = {
    "pecs": "muscle:chest",
    "pectorals": "muscle:chest",
    "abs": "muscle:core",
    "quadriceps": "muscle:quads",
    "glutes max": "muscle:glutes",
    "shoulders": "muscle:deltoids",
    "db": "equipment:Dumbbell",
    "dumbbells": "equipment:Dumbbell",
    "kettlebells": "equipment:Kettlebell",
    "kb": "equipment:Kettlebell",
    "pull up bar": "equipment:Pull-Up Bar",
}

EmbedFn = Callable[[str, list[str]], list[tuple[str, float]]]


@dataclass
class ResolvedConcept:
    query: str
    node_id: str | None
    method: str  # exact | fuzzy | embedding | none
    confidence: float
    passes_tried: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _candidate_index() -> dict[str, str]:
    """lowercased candidate name -> node id, for concept kinds the coach can reference."""
    g = build_movement_graph()
    index: dict[str, str] = {}
    for nid, data in g.nodes(data=True):
        if data["kind"] in {
            Kind.MUSCLE,
            Kind.JOINT,
            Kind.EQUIPMENT,
            Kind.MOVEMENT_PATTERN,
            Kind.EXERCISE,
        }:
            index[data["name"].lower()] = nid
    # Region aliases map onto joints — safety-relevant, so they take priority.
    for alias, joint in REGION_ALIASES.items():
        index[alias.lower()] = f"joint:{joint}"
    return index


def resolve(query: str, embed_fn: EmbedFn | None = None) -> ResolvedConcept:
    q = query.strip().lower()
    index = _candidate_index()
    tried: list[str] = []

    # Pass 1 — exact: canonical names, region aliases, curated synonyms.
    tried.append("exact")
    if q in index:
        return ResolvedConcept(query, index[q], "exact", 1.0, tried)
    if q in SYNONYMS:
        return ResolvedConcept(query, SYNONYMS[q], "exact", 1.0, tried)

    # Pass 2 — fuzzy (typos, near-misses).
    tried.append("fuzzy")
    match = process.extractOne(q, index.keys(), scorer=fuzz.WRatio)
    if match is not None:
        name, score, _ = match
        confidence = score / 100.0
        if confidence >= FUZZY_FLOOR:
            return ResolvedConcept(query, index[name], "fuzzy", round(confidence, 3), tried)

    # Pass 3 — embedding fallback (semantic paraphrases).
    tried.append("embedding")
    if embed_fn is not None:
        ranked = embed_fn(q, list(index.values()))
        if ranked:
            node_id, sim = ranked[0]
            if sim >= EMBEDDING_FLOOR:
                return ResolvedConcept(query, node_id, "embedding", round(sim, 3), tried)

    # Graceful degradation: report the attempt, never guess.
    return ResolvedConcept(query, None, "none", 0.0, tried)
