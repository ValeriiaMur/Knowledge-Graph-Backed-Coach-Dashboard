# Project Summary — KG-Backed Coach Dashboard (living doc)

> Single source of truth for status, decisions, and plan. Update on every working session.
> Spec: [ASSESSMENT.md](./ASSESSMENT.md) · Scoping: [PRESEARCH.md](./PRESEARCH.md) · Diagram: [system-design.svg](./system-design.svg) · Rules: [AGENT_RULES.md](./AGENT_RULES.md)

**Last updated:** 2026-06-04 · **Status:** phase 5 complete, phase 6 (UI + nice-to-haves) next

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
| 6 | UI polish + nice-to-haves | Graph viz, streaming, trace view, eval script | 2h | ☐ |
| 7 | README + examples | Diagram, trade-offs, 3 worked examples, runthrough test | 1.5h | ☐ |

Critical path: phases 2–3 — everything downstream consumes the graphs and the safety filter, and they carry the heaviest evaluation weight.

## Acceptance scenarios (from spec — must demo)

1. "Exclude deadlifts" → no deadlift variations appear.
2. "Her left knee is bothering her" → knee-loading exercises excluded/down-ranked via the anatomy `part-of` hierarchy.
3. "No barbell, only dumbbells + kettlebell" → barbell-only exercises dropped, equivalent alternatives found.
4. Every plan ships a provenance trace; copilot answers grounded in member-context.json.

## Open questions

- (none — resolved during pre-search; add new ones here as they come up)

## Changelog

- **2026-06-04** — Phase 5 done: copilot — 13 grounded retrieval tools over KG 2 (brief, adherence, churn, sleep, biomarkers, labs, injuries, goals, prefs, chats, workouts, what-changed, timeseries w/ honest unknown-metric error); agent tool-use loop (injectable LLM, session history, unknown-tool resilience, iteration cap); Anthropic adapter; endpoints /api/copilot/chat, /quick-prompts, /chat-history, /api/member/timeseries/{metric}. 54 tests green, lint clean, endpoints verified live.

- **2026-06-04** — Phase 4 done: agentic runtime — constraints derived from KG 2 (injury/condition/equipment auto-applied) + deterministic prompt scanning w/ honest unresolved reporting; LLM composer injectable (fake in tests, Claude tool-use `submit_plan` in prod); plans referencing filtered exercises rejected by validation; provenance + timed trace on every generation; POST /api/generate wired. 42 tests green, lint clean. Needs ANTHROPIC_API_KEY in .env for live generation.

- **2026-06-04** — Phase 3 done: resolver (exact w/ synonyms+aliases → fuzzy ≥0.85 → embedding ≥0.75, injectable embed_fn, Voyage wiring with graceful degradation, honest no-match) + safety filter (pure traversal: explicit exclusions, injury part-of expansion, condition exclude/down-rank, equipment + substitutes sharing muscle∧pattern; provenance path on every removal). 34 tests green, lint clean.

- **2026-06-04** — Phase 2 done: KG 1 (50 exercises, 19 muscles, 9 joints w/ SNOMED SKOS mappings, 32 equipment, 36 patterns, anatomy part-of hierarchy, PFPS condition with exclude/down-rank contraindications) + KG 2 (member, injury→joint:knee bridge, equipment refs, goals/sessions/chats). 16 tests red→green, lint clean. Schema documented in docs/KG_SCHEMA.md.

- **2026-06-04** — Phase 1 done: backend (FastAPI, typed Pydantic models, data loader — 5 tests red→green, ruff clean), frontend (Vite + React strict TS, eslint/prettier clean, tsc passes), Makefile targets (install/dev/test/lint/eval), .env.example, CLAUDE.md. Verified live: /api/health ok, /api/exercises serves 50, /api/member serves full context.
- **2026-06-04** — Planning session: requirements brainstormed, pre-search checklist filled (PDF + PRESEARCH.md), system-design SVG drawn, agent rules defined, phases locked.
