# Project Summary — KG-Backed Coach Dashboard (living doc)

> Single source of truth for status, decisions, and plan. Update on every working session.
> Spec: [ASSESSMENT.md](./ASSESSMENT.md) · Scoping: [PRESEARCH.md](./PRESEARCH.md) · Diagram: [system-design.svg](./system-design.svg) · Rules: [AGENT_RULES.md](./AGENT_RULES.md)

**Last updated:** 2026-06-05 · **Status:** all 7 phases complete — README shipped, design-system UI live, token streaming in

---

## What we're building

Coach-facing dashboard for Future's take-home: (A) a workout generator driven by a movement/clinical knowledge graph with deterministic graph-traversal safety filtering and provenance traces, and (B) an AI copilot retrieving over a member-context knowledge graph. 1-day timebox.

## Locked decisions

| Decision | Choice |
|---|---|
| Graph store | In-process NetworkX, JSON persistence |
| Stack | Python FastAPI backend + React/Vite frontend (strict TS) |
| LLM | Anthropic API, hand-rolled tool-use orchestrator (no framework) |
| Embeddings | Voyage AI (resolver pass 3) |
| Ontology grounding | Hand-rolled schema + curated SNOMED/OPE lookup table, SKOS mappings, no live API |
| Run | Makefile / single script, .env for keys |
| Nice-to-haves in scope | Graph viz, streaming, observability traces, eval pipeline |
| Resolver thresholds | fuzzy ≥ ~0.85, embedding cosine ≥ ~0.75, else no-match (tune + document) |

## Phases of work

| # | Phase | Work | ~Time | Status |
|---|---|---|---|---|
| 1 | Foundations | Repo scaffold, Makefile, FastAPI + Vite shells, load both JSONs | 1h | ✅ |
| 2 | KG 1 + KG 2 | NetworkX graphs, schema doc, SNOMED/OPE mapping table | 2h | ✅ |
| 3 | Resolver + safety filter | 3-pass resolver with thresholds, traversal filter, pytest both | 2h | ✅ |
| 4 | Agentic runtime | Tool-use loop, plan composer, provenance trace | 2h | ✅ |
| 5 | Copilot | Retrieval over KG 2, quick prompts, charts, chat history | 2h | ✅ |
| 6 | UI polish + nice-to-haves | Graph viz, streaming, trace view, eval script | 2h | ✅ (streaming deferred — see Open questions) |
| 7 | README + examples | Diagram, trade-offs, 3 worked examples, runthrough test | 1.5h | ✅ |

Critical path: phases 2–3 — everything downstream consumes the graphs and the safety filter, and they carry the heaviest evaluation weight.

## Acceptance scenarios (from spec — must demo)

1. "Exclude deadlifts" → no deadlift variations appear.
2. "Her left knee is bothering her" → knee-loading exercises excluded/down-ranked via the anatomy `part-of` hierarchy.
3. "No barbell, only dumbbells + kettlebell" → barbell-only exercises dropped, equivalent alternatives found.
4. Every plan ships a provenance trace; copilot answers grounded in member-context.json.

## Open questions

- ~~Token-level streaming deferred from phase 6~~ → **Resolved 2026-06-05:** implemented for copilot chat (SSE `token`/`tool`/`done` events, injectable stream LLM, 5 new tests, non-streaming client fallback). Generation intentionally stays atomic — plans are validated before display.

## Changelog

- **2026-06-05** — Spec-gap closure (4 gaps from a line-by-line requirements audit): (1) chat image attachments now survive KG 2 → `get_chat_history` → copilot UI (DS attachment card w/ caption; spec "chat with history/images" — the planted home-setup photo renders); (2) inclusion-side provenance: `provenance.selected` records why each chosen exercise made the plan (graph path, matched prompt concepts, tier, passed-filter attestation), rendered in the Generate tab and regenerated into docs/worked-examples.json; (3) PROV-O alignment table (Activity/Entity/Agent/wasDerivedFrom mapping) added to KG_SCHEMA.md; (4) per-ontology pull/leave-out reasoning (SNOMED, SKOS, PROV-O, OPE, COPPER) documented in KG_SCHEMA.md + README pointers. 69 tests green, lint clean.

- **2026-06-05** — Longitudinal reasoning (nice-to-have) shipped: pure trend module `app/copilot/longitudinal.py` (adherence slope/deltas, volume, RPE direction, weight delta, sleep avg + one-line summary), exposed as `get_progression` copilot tool (14 tools now, "How is she progressing?" quick prompt) and injected as `member_progression` into the generator payload when member context is on — guidance only, safety stays in the filter. 6 new tests red→green (67 total), ruff clean, eval still 15/15 · 3/3 · 3/3. Multi-agent orchestration consciously left as the one unbuilt nice-to-have, documented with its extension path in README trade-offs.

- **2026-06-05** — Requirements sweep: plan-quality eval added to `make eval` (structural checks on full generations, offline composer — now resolver 15/15 · safety 3/3 · plan quality 3/3); README gained the two remaining required sections ("Testing & evals" incl. production evaluation/metrics/failure modes, and "How AI was used to build this"). Spec deliverables now fully covered.

- **2026-06-05** — Phase 7 done: README.md (quickstart, architecture, why-this-tech rationale, scaling table, 3 worked examples from real pipeline output in docs/worked-examples.json, trade-offs incl. honest resolver false-positive + no-deadlifts-in-catalog notes). Token streaming shipped (backend `run_copilot_stream` + `/api/copilot/chat/stream`, frontend SSE consumer). Graph node detail popover: `/api/graph` now returns full node attrs (SNOMED SKOS mappings, priority tier, bilateral) + edge `mode`; floating DS card shows attrs and grouped relations with click-to-jump. 61 backend tests green, eval 15/15 + 3/3, both lints clean, vite build passes.

- **2026-06-05** — Design-system UI session: Future DS handoff (future-ds.css, dashboard.css, dash-*.jsx) ported 1:1 into the frontend as the app shell. Designed dashboard grid fully wired to real data via pure derivations (src/derive.ts) — stat pills (adherence/HRV/sleep/RHR), KPIs and progress bars from workout history, timer from preferred session minutes, accordions (equipment/injuries/goals/prefs), calendar from history + preferred days + brief, session card shows generated plan (state lifted to App) with history fallback. Generator/Copilot/Graph/Login redesigned with DS primitives as nav tabs. MemberHeader + old index.css removed (replaced by Hero/ProfileCard). SSR smoke-test against real member-context.json; tsc/eslint/prettier/build green.

- **2026-06-04** — Phase 6 done: eval pipeline (`make eval`: resolver 15/15, safety 3/3); /api/graph endpoint (161 nodes, 424 links); full dashboard UI — 11 components, one per file (LoginGate mock auth, MemberHeader badges, BriefCard, GeneratorPanel→PlanView+ProvenanceTrace w/ graph paths + pipeline timings, CopilotPanel w/ member chat history + grounded tool-call labels, QuickPrompts, TrendChart SVG, GraphView radial KG viz w/ click-to-highlight edges). Chart prompts render deterministically from timeseries endpoints (no LLM). tsc, eslint, prettier clean; vite build passes. Token streaming deferred.

- **2026-06-04** — Phase 5 done: copilot — 13 grounded retrieval tools over KG 2 (brief, adherence, churn, sleep, biomarkers, labs, injuries, goals, prefs, chats, workouts, what-changed, timeseries w/ honest unknown-metric error); agent tool-use loop (injectable LLM, session history, unknown-tool resilience, iteration cap); Anthropic adapter; endpoints /api/copilot/chat, /quick-prompts, /chat-history, /api/member/timeseries/{metric}. 54 tests green, lint clean, endpoints verified live.

- **2026-06-04** — Phase 4 done: agentic runtime — constraints derived from KG 2 (injury/condition/equipment auto-applied) + deterministic prompt scanning w/ honest unresolved reporting; LLM composer injectable (fake in tests, Claude tool-use `submit_plan` in prod); plans referencing filtered exercises rejected by validation; provenance + timed trace on every generation; POST /api/generate wired. 42 tests green, lint clean. Needs ANTHROPIC_API_KEY in .env for live generation.

- **2026-06-04** — Phase 3 done: resolver (exact w/ synonyms+aliases → fuzzy ≥0.85 → embedding ≥0.75, injectable embed_fn, Voyage wiring with graceful degradation, honest no-match) + safety filter (pure traversal: explicit exclusions, injury part-of expansion, condition exclude/down-rank, equipment + substitutes sharing muscle∧pattern; provenance path on every removal). 34 tests green, lint clean.

- **2026-06-04** — Phase 2 done: KG 1 (50 exercises, 19 muscles, 9 joints w/ SNOMED SKOS mappings, 32 equipment, 36 patterns, anatomy part-of hierarchy, PFPS condition with exclude/down-rank contraindications) + KG 2 (member, injury→joint:knee bridge, equipment refs, goals/sessions/chats). 16 tests red→green, lint clean. Schema documented in docs/KG_SCHEMA.md.

- **2026-06-04** — Phase 1 done: backend (FastAPI, typed Pydantic models, data loader — 5 tests red→green, ruff clean), frontend (Vite + React strict TS, eslint/prettier clean, tsc passes), Makefile targets (install/dev/test/lint/eval), .env.example, CLAUDE.md. Verified live: /api/health ok, /api/exercises serves 50, /api/member serves full context.
- **2026-06-04** — Planning session: requirements brainstormed, pre-search checklist filled (PDF + PRESEARCH.md), system-design SVG drawn, agent rules defined, phases locked.
