# Agent Rules — KG-Backed Coach Dashboard

Rules for any coding agent (and human) working on this repo. Copy into the build repo as `CLAUDE.md` when scaffolding.

## 1. Strict TypeScript (frontend)

- `tsconfig.json`: `"strict": true`, plus `noUncheckedIndexedAccess` and `noImplicitOverride`.
- No `any` (implicit or explicit), no `@ts-ignore`/`@ts-expect-error` without an inline justification comment.
- API contracts typed end-to-end: shared types generated or mirrored from FastAPI's Pydantic models — never hand-wave the boundary.

## 2. Red-Green TDD

- Write the failing test first (red), implement the minimum to pass (green), then refactor.
- Applies strictly to the deterministic core: concept resolver, safety filter, equipment substitution, graph builders.
- LLM-composition code is tested structurally (schema-valid output, no filtered exercises present), not string-matched.
- Never mark work done with failing tests; never weaken a test to make it pass.

## 3. One component per file

- Each React component lives in its own file, named after the component (`ProvenanceTrace.tsx` exports `ProvenanceTrace`).
- Pages compose components; no multi-component dump files, no inline mega-components.
- Same spirit in Python: one module = one responsibility (resolver, traversal, composer, retrieval are separate modules).

## 4. Lint + format on every change

- Run on every change, before every commit — not as a cleanup pass at the end:
  - Frontend: `eslint` + `prettier`
  - Backend: `ruff check` + `ruff format`
- `make lint` runs all of the above; zero warnings is the bar.
- Pair with `make test` — lint + tests green is the definition of "change complete".

## Standing constraints (from the spec)

- Safety decisions are graph traversals, never prompt instructions — the LLM only sees pre-filtered candidates.
- Every generated plan must carry a provenance trace.
- Synthetic data only; never real member data.
- Copilot answers must be grounded in the member-context KG — "not in this member's context" beats a guess.
