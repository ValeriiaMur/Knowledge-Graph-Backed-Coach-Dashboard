"""Phase 3 (red-green): concept resolver — exact → fuzzy → embedding, with
explicit confidence thresholds and graceful no-match. Embedding pass is injected
so tests run offline (CLAUDE.md: deterministic core gets strict TDD)."""

from app.resolver.resolver import ResolvedConcept, resolve

# --- pass 1: exact (incl. aliases) -----------------------------------------


def test_exact_match_joint():
    r = resolve("knee")
    assert r.node_id == "joint:knee"
    assert r.method == "exact"
    assert r.confidence == 1.0


def test_alias_resolves_to_canonical_node():
    r = resolve("lower back")  # muscle name AND region alias — region wins for safety
    assert r.node_id in {"joint:lumbar spine", "muscle:lower back"}
    assert r.method == "exact"


def test_synonym_pecs_resolves_to_chest():
    r = resolve("pecs")
    assert r.node_id == "muscle:chest"
    assert r.method == "exact"  # curated synonym table counts as exact


def test_equipment_case_insensitive():
    r = resolve("kettlebell")
    assert r.node_id == "equipment:Kettlebell"
    assert r.method == "exact"


# --- pass 2: fuzzy ----------------------------------------------------------


def test_fuzzy_catches_typo():
    r = resolve("ketlebell")
    assert r.node_id == "equipment:Kettlebell"
    assert r.method == "fuzzy"
    assert r.confidence >= 0.85


def test_fuzzy_threshold_rejects_weak_match():
    """Below the fuzzy floor we must NOT guess — fall through to embedding/no-match."""
    r = resolve("zzqxv")
    assert r.method == "none"
    assert r.node_id is None


# --- pass 3: embedding (injected) -------------------------------------------


def test_embedding_fallback_used_when_fuzzy_fails():
    def fake_embed(text: str, candidates: list[str]) -> list[tuple[str, float]]:
        return [("joint:knee", 0.92)]

    r = resolve("the hinge joint in my leg", embed_fn=fake_embed)
    assert r.node_id == "joint:knee"
    assert r.method == "embedding"
    assert r.confidence == 0.92


def test_embedding_below_floor_degrades_to_no_match():
    def fake_embed(text: str, candidates: list[str]) -> list[tuple[str, float]]:
        return [("joint:knee", 0.40)]

    r = resolve("completely unrelated gibberish", embed_fn=fake_embed)
    assert r.method == "none"
    assert r.node_id is None
    assert "embedding" in r.passes_tried


def test_no_match_reports_all_passes_tried():
    r = resolve("flibbertigibbet")
    assert r.method == "none"
    assert r.passes_tried == ["exact", "fuzzy", "embedding"]


# --- multi-concept extraction ------------------------------------------------


def test_resolve_returns_typed_result():
    r = resolve("knee")
    assert isinstance(r, ResolvedConcept)
    assert r.query == "knee"
