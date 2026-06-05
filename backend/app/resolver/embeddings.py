"""Production pass-3 embedder (Voyage AI). Lazy client, cached candidate vectors.
If VOYAGE_API_KEY is missing or the call fails, returns [] — the resolver then
degrades to exact+fuzzy and logs degraded mode (PRESEARCH §11)."""

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

_MODEL = "voyage-3-lite"


@lru_cache(maxsize=1)
def _client():
    import voyageai

    return voyageai.Client()  # reads VOYAGE_API_KEY


@lru_cache(maxsize=1)
def _candidate_vectors() -> tuple[list[str], list[list[float]]]:
    from app.resolver.resolver import _candidate_index

    index = _candidate_index()
    names = list(index.keys())
    node_ids = [index[n] for n in names]
    vectors = _client().embed(names, model=_MODEL, input_type="document").embeddings
    return node_ids, vectors


def voyage_embed(text: str, candidates: list[str]) -> list[tuple[str, float]]:
    if not os.environ.get("VOYAGE_API_KEY"):
        logger.warning("resolver degraded: VOYAGE_API_KEY not set, skipping embedding pass")
        return []
    try:
        node_ids, vectors = _candidate_vectors()
        qvec = _client().embed([text], model=_MODEL, input_type="query").embeddings[0]
        norm_q = sum(x * x for x in qvec) ** 0.5
        scored = []
        for nid, vec in zip(node_ids, vectors, strict=True):
            dot = sum(a * b for a, b in zip(qvec, vec, strict=True))
            norm_v = sum(x * x for x in vec) ** 0.5
            scored.append((nid, dot / (norm_q * norm_v)))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:5]
    except Exception:
        logger.exception("resolver degraded: embedding pass failed")
        return []
