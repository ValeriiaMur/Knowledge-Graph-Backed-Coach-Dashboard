# Project Summary — KG-Backed Coach Dashboard (living doc)

> Single source of truth for status, decisions, and plan. Update on every working session.
> Spec: [ASSESSMENT.md](./ASSESSMENT.md) · Scoping: [PRESEARCH.md](./PRESEARCH.md) · Diagram: [system-design.svg](./system-design.svg) · Rules: [AGENT_RULES.md](./AGENT_RULES.md)

**Last updated:** 2026-06-04 · **Status:** planning complete, build not started

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
| 1 | Foundations | Repo scaffold, Makefile, FastAPI + Vite shells, load both JSONs | 1h | ☐ |
| 2 | KG 1 + KG 2 | NetworkX graphs, schema doc, SNOMED/OPE mapping table | 2h | ☐ |
| 3 | Resolver + safety filter | 3-pass resolver with thresholds, traversal filter, pytest both | 2h | ☐ |
| 4 | Agentic runtime | Tool-use loop, plan composer, provenance trace | 2h | ☐ |
| 5 | Copilot | Retrieval over KG 2, quick prompts, charts, chat history | 2h | ☐ |
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

- **2026-06-04** — Planning session: requirements brainstormed, pre-search checklist filled (PDF + PRESEARCH.md), system-design SVG drawn, agent rules defined, phases locked.
