# Future Coach — KG-Backed Coach Dashboard

A coach-facing dashboard built around one idea: **safety decisions are graph traversals, never prompt instructions.** The LLM composes workouts only from candidates that a deterministic knowledge-graph filter has already approved, and every plan ships with a provenance trace explaining exactly what was removed and why. A copilot answers questions about the member grounded entirely in a member-context knowledge graph — "not in this member's context" beats a guess.

Built in a 1-day timebox on synthetic data only. Spec: [ASSESSMENT.md](./ASSESSMENT.md) · Scoping: [PRESEARCH.md](./PRESEARCH.md) · Status log: [SUMMARY.md](./SUMMARY.md) · Diagram: [system-design.svg](./system-design.svg)

---

## Quickstart

```bash
make install                 # backend: pip install -e ".[dev]" · frontend: npm install
cp .env.example .env         # add ANTHROPIC_API_KEY (and optionally VOYAGE_API_KEY)
make dev                     # backend :8000 + frontend :5173
```

Open http://localhost:5173, log in with any coach name (mock auth per spec), and you land on the dashboard.

Other targets: `make test` (61 backend tests) · `make lint` (ruff + eslint + prettier, zero-warning bar) · `make eval` (resolver 15/15 · safety 3/3 · plan quality 3/3).

Without `ANTHROPIC_API_KEY` everything deterministic still works — member dashboard, graph view, chart prompts, and the full safety/provenance pipeline; only LLM plan composition and free-form copilot chat need the key. `VOYAGE_API_KEY` enables the resolver's third (embedding) pass; without it the resolver degrades gracefully to exact + fuzzy.

## Architecture

```
data/exercises.json ──► KG 1: movement/clinical graph (NetworkX)
data/member-context.json ──► KG 2: member-context graph
                                    │
coach prompt ──► resolver (exact → fuzzy → embedding) ──► constraints
                                    │
                  safety filter — pure graph traversal
                  (exclusions · injury part-of expansion ·
                   condition contraindications · equipment + substitutes)
                                    │
                  allowed candidates ──► LLM composer (tool-use, injectable)
                                    │            │
                  validation (no filtered IDs) ◄─┘
                                    │
                  plan + provenance trace + timed pipeline trace
```

- **KG 1 (movement/clinical):** 161 nodes, 424 edges — exercises, muscles, joints, anatomy `part_of` hierarchy, equipment, movement patterns, and conditions with `contraindicated_for` edges (`exclude` vs `down_rank`). Joints and conditions carry SKOS mappings to SNOMED CT (curated lookup table, no live terminology API).
- **KG 2 (member context):** profile, injury→joint bridge (`left knee` → `joint:knee`), equipment, goals, sessions, chats. Member constraints (injury, condition, available equipment) are **auto-applied** to every generation — the coach doesn't have to remember them.
- **Resolver:** 3 passes — exact (with synonyms/aliases) → fuzzy ≥ 0.85 → embedding cosine ≥ 0.75 (Voyage). Below threshold means an honest no-match surfaced to the coach, never a silent drop.
- **Copilot:** hand-rolled Anthropic tool-use loop over 13 retrieval tools on KG 2. The model never sees raw member data outside tool results — grounding by construction. Member chat text returned by tools is treated as quoted data, not instructions (prompt-injection stance). Replies stream token-by-token over SSE.
- **Frontend:** React + Vite, strict TypeScript (`noUncheckedIndexedAccess`), one component per file. The whole UI is built on the **Future DS** design system (`frontend/src/styles/future-ds.css` — tokens, accent variants, dark theme, pill/card/tag primitives); the dashboard renders only data derived from `/api/member` and `/api/generate` via pure functions in `src/derive.ts` — no hardcoded member data anywhere.

## Why this tech, and why this way

**NetworkX in-process instead of a graph database.** The graph is ~10² nodes and read-only at runtime. An embedded structure gives microsecond traversals, zero ops, and trivially testable pure functions. A graph DB would add a service, a query language, and network latency to buy capabilities (scale, concurrent writes) this stage doesn't need. The graph builders are isolated modules, so the swap path is clean (see Scaling).

**Safety as traversal, not prompting.** LLMs are probabilistic; injury contraindications must not be. The filter runs *before* the model sees anything, so a jailbreak, a bad sample, or a hallucination cannot reintroduce a knee-loading exercise — validation also rejects any plan referencing a filtered ID as defense in depth. The LLM is used only for what it's good at: composing a sensible session from pre-approved candidates.

**Hand-rolled tool-use loop instead of an agent framework.** The loop is ~60 lines, fully typed, offline-testable with a fake LLM, and owns its failure modes (unknown tool → honest error result; iteration cap → explicit "narrow your question"). Frameworks hide exactly the control flow this project needs to demonstrate.

**FastAPI + Pydantic / strict TS, mirrored contracts.** Types end-to-end across the HTTP boundary (CLAUDE.md §1) — the frontend's `types.ts` mirrors the backend's Pydantic models, so contract drift is a compile error, not a runtime surprise.

**Injectable LLMs everywhere.** Both the composer and the copilot take the model call as a function argument. Tests inject deterministic fakes (red-green TDD on the deterministic core); production injects the Anthropic adapters. The streaming variant follows the same contract (`token…` then `final`), so the loop logic is tested without a network.

**Deterministic chart prompts.** "Plot adherence trend" renders straight from the timeseries endpoint with zero LLM round-trip — instant, always grounded, and immune to hallucinated numbers.

**Curated SNOMED lookup instead of a live terminology server.** SKOS mappings (`exactMatch`/`closeMatch`, verified flags) are stored on the nodes. This keeps the demo hermetic while preserving the ontology-grounding shape a production system would need.

## How this scales

| Dimension | Today (demo) | Scale path |
|---|---|---|
| Graph store | NetworkX in-process, JSON seed | Builders are isolated modules → swap to a property graph (Neo4j/Memgraph) when the catalog reaches ~10⁵ nodes or needs concurrent writes; traversal queries map 1:1 to Cypher. The safety filter's contract (candidates in → allowed + provenance out) doesn't change. |
| Members | One synthetic member, KG 2 rebuilt per process | KG 2 becomes a per-member subgraph keyed by tenant; build on ingest, cache hot members. Member endpoints already take no global state besides the loader. |
| Sessions | In-memory dict | Move copilot session history to Redis with TTL; the agent loop already treats history as a plain list. |
| Resolver | Voyage embeddings computed per call | Precompute catalog embeddings into a vector index (pgvector/FAISS); thresholds stay, only the lookup changes. |
| Ontology | Curated SNOMED table | Sync from a terminology server (e.g. NCI EVS / Snowstorm) into the same SKOS shape; `verified` flags drive review queues. |
| Serving | uvicorn, single process | API is stateless (sessions externalized) → horizontal replicas behind a load balancer; SSE streams are per-request and proxy-friendly. |
| Safety evolution | 3 eval scenarios, 61 tests | The eval pipeline (`make eval`) is the regression gate: every new contraindication rule or catalog import must keep resolver/safety scores green in CI before deploy. |
| Observability | Timed pipeline traces per generation, structured logs | Same trace events → OpenTelemetry spans; provenance objects are already the audit log a clinical reviewer would ask for. |
| Auth | Mock login (any name) | Real IdP (OIDC) with coach→member authorization checks at the member-context boundary. |

## Worked examples

Full machine-readable outputs: [docs/worked-examples.json](./docs/worked-examples.json) (generated with the deterministic offline composer so they're reproducible without an API key — the safety/provenance behavior is identical with the live LLM, which only chooses *among* already-approved candidates).

### 1 · "Full-body strength, exclude deadlifts"

The exclusion term is captured (`excluded_terms: ["deadlift"]`) and would remove any matching exercise. Honest note: the 50-exercise catalog contains **no** deadlift variations, so nothing matches — the pipeline proves itself instead on the member's auto-applied constraints: 40 of 50 exercises removed (17 equipment, 21 knee-injury, 2 condition), 10 allowed.

### 2 · "Lower-body session, her left knee is bothering her"

Resolver (fuzzy pass): `"her left knee" → joint:knee (0.95)`. The injury expands through the anatomy hierarchy and removes 21 knee-loading exercises, each with its graph path, e.g.:

```text
Kettlebell Goblet Cyclist Squat — injury
exercise:… -stresses-> joint:knee (expanded via part_of: patellofemoral joint)
substitutes: Hip Thrust, Banded Lateral Walk
```

The member's PFPS condition adds `contraindicated_for` removals (plyometrics excluded, squat patterns down-ranked). Composition then only ever sees the 10 survivors.

### 3 · "Upper-body push, no barbell, only dumbbells and kettlebell"

`"no barbell" → equipment:Barbell (0.90)` becomes an explicit exclusion — all 3 barbell exercises removed with reason `coach said exclude "barbell"`. Equipment traversal drops 16 more (bench/pull-up-bar/machine requirements ∉ available equipment), each listing substitutes that share muscle ∧ movement pattern, e.g. `Dumbbell Neutral-Grip Bench Press` replacing the barbell press.

Known resolver limit, kept honest: in this prompt the fuzzy pass also matched `"upper-body push" → movement_pattern:lower push - calf raise (0.855)` — a false positive just above threshold. It's reported in `resolved_concepts` (never silently acted on as an exclusion), and the embedding pass + threshold tuning is the documented fix.

### Reproduce

```bash
curl -s localhost:8000/api/generate -X POST -H 'Content-Type: application/json' \
  -d '{"prompt": "lower-body, her left knee is bothering her", "minutes": 30}' | python3 -m json.tool
```

or use the **Generate** tab — the provenance card renders resolved concepts, removals with graph paths, substitutes, and pipeline timings; the generated plan also appears on the dashboard's session card.

## Testing & evals

**Unit tests (61, red-green TDD on the deterministic core).** The spec mandates tests for the resolver and safety filter at minimum; those are the critical paths because they make the safety guarantees — a resolver false negative silently drops a coach's constraint, and a filter bug is exactly the unsafe-recommendation failure the project exists to prevent. Coverage: resolver (10), safety filter (8), both KG builders (11), runtime/validation (8), copilot tools + agent loop (12), streaming loop (5), data loader (5), graph endpoint (2). LLM-composition code is tested *structurally* (schema-valid output, no filtered exercise present) — never string-matched.

**Eval pipeline (`make eval`)** — the regression gate, runs offline (no API key):

- *Resolver accuracy* — 15 hand-labeled queries incl. typos ("ketlebell") and must-no-match nonsense terms: 15/15.
- *Safety correctness* — the 3 acceptance scenarios verified against the graph (no allowed exercise stresses the injured joint / requires unavailable equipment / matches an excluded term): 3/3.
- *Plan quality* — structural checks on full generations (warmup/main/cooldown present, no filtered IDs, sane doses, non-empty provenance): 3/3.

**Evaluating in production — metrics, failure modes, monitoring:**

- *Safety (the metric that matters):* zero plans containing a filtered exercise — enforced at runtime by validation, monitored by logging every rejection; any occurrence is a sev-1. Track contraindication-rule coverage as the catalog grows.
- *Resolver quality:* precision/recall on a growing labeled set from real coach prompts; alert on rising no-match rate (vocabulary drift) and on near-threshold matches (the documented 0.85-fuzzy false-positive band) — sample those for human review.
- *Copilot grounding:* fraction of replies with ≥1 tool call; "not in this member's context" rate vs. hallucination spot-checks; periodic LLM-as-judge pass over sampled transcripts scored against tool outputs.
- *Latency & cost:* the per-stage timed trace (resolve → filter → compose) already separates deterministic time (~2 ms) from LLM time; alert when compose p95 exceeds the ~5 s budget. Token usage logged per call.
- *Failure modes watched:* over-filtering (allowed_count → 0 spikes), composer schema violations (rejected-plan rate), tool errors in the agent loop, SSE disconnects.

## Trade-offs & known limits

- **Token streaming** is implemented for copilot chat (SSE: `token` / `tool` / `done` events, non-streaming fallback in the client). Generation is *not* streamed — plans are validated atomically before anything is shown, which is the safer UX for a clinical-ish artifact.
- **Resolver false positives near threshold** (see example 3). Tuning data: `make eval` keeps resolver accuracy visible; thresholds live in one place.
- **No deadlifts in the catalog** makes acceptance scenario 1 trivially pass; the mechanism is exercised by the barbell scenario instead.
- **Calendar time rows are scaffold** — workout history has dates but no time-of-day, so events place into a fixed 6:00–10:00 grid deterministically.
- **Mock auth, single member, synthetic data only** — per spec; see Scaling for the real-auth path.
- **Timer state in `localStorage`** — fine for a demo; would move server-side with real sessions.

## How AI was used to build this

The project was built by pairing with Claude (Cowork/Claude Code) under the rules in [CLAUDE.md](./CLAUDE.md): red-green TDD on the deterministic core (failing test first, then the implementation), strict typing end-to-end, one component per file, lint + tests green before any change counts as done. The workflow per phase: brainstorm and lock decisions into [PRESEARCH.md](./PRESEARCH.md)/[SUMMARY.md](./SUMMARY.md), have the agent implement against those constraints, then verify with `make test`, `make lint`, `make eval` and live API smoke tests. The dashboard UI was generated from a Future DS design handoff (design system + mockups) and re-implemented as typed React components wired to real API data — with an SSR smoke-render against the real member JSON as the visual sanity check. All worked examples in this README are captured pipeline output, not hand-written. AI is also *in* the product with the same philosophy it was built under: the LLM composes and converses, but never decides safety.

## Repo layout

```
backend/app/      graph/ (KG builders) · resolver/ · safety/ · runtime/ (generator)
                  copilot/ (tools + agent loop + Anthropic adapters) · eval/
backend/tests/    61 tests — red-green TDD on the deterministic core
frontend/src/     styles/ (Future DS) · components/ (one per file) · derive.ts (pure view-models)
data/             exercises.json · member-context.json (synthetic)
docs/             KG_SCHEMA.md · worked-examples.json
```
