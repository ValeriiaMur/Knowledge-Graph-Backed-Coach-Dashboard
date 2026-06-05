# Knowledge Graph Schema

Both graphs are in-process NetworkX `MultiDiGraph`s. Node ids are `kind:name`
(e.g. `joint:knee`, `exercise:ex_001`) — the same id scheme in both graphs, which is
how KG 2 anchors onto KG 1 canonical concepts.

## KG 1 — Movement / Clinical (`app/graph/movement_kg.py`)

### Node kinds

| Kind | Source | Meaning | Key attrs |
|---|---|---|---|
| `exercise` | exercises.json (50) | A catalog exercise | name, priority_tier, is_bilateral, side |
| `muscle` | derived from catalog (19) | Canonical muscle group | name |
| `joint` | derived from catalog (9) | Canonical joint / body region | name, **skos_mappings** (SNOMED CT) |
| `substructure` | curated ontology table | Anatomical part of a joint (patella, ACL…) | name |
| `equipment` | derived from catalog (32) | Equipment type | name |
| `movement_pattern` | derived from catalog (36) | Movement taxonomy entry | name |
| `condition` | curated ontology table | Clinical condition (e.g. patellofemoral pain syndrome) | name, skos_mappings |

### Edge rels

| Rel | From → To | Meaning / why it exists |
|---|---|---|
| `targets` | exercise → muscle | What the exercise trains — drives prompt matching ("isolation around my pecs") |
| `stresses` | exercise → joint | What the exercise loads — the safety-relevant edge |
| `requires` | exercise → equipment | Hard equipment dependency — drives availability filtering + substitution |
| `follows` | exercise → movement_pattern | Taxonomy membership — drives contraindication expansion + variety |
| `part_of` | substructure → joint | Anatomy hierarchy — "knee" covers patella, ACL, meniscus… (spec requirement) |
| `located_in` | condition → substructure | Where a condition lives anatomically |
| `contraindicated_for` | condition → movement_pattern | Unsafe patterns; attr `mode`: `exclude` (hard) or `down_rank` (caution) |

### Ontology grounding (SKOS)

`joint` and `condition` nodes carry `skos_mappings`: `{scheme, code, label, match, verified}`.
Six joint→SNOMED CT mappings are verified exact matches (knee 49076000, shoulder 16982005,
hip 24136001, elbow 16953009, wrist 74670003, ankle 70258002); spine segments and conditions
are `skos:closeMatch` with `verified: false` — to be confirmed via NCI EVS before any
production claim. Curated table lives in `app/graph/ontology.py`. Decision rationale:
PRESEARCH §6–7 — a small table used meaningfully over shallow full-OWL ingestion.

## KG 2 — Member Context (`app/graph/member_kg.py`)

### Node kinds

| Kind | Source | Key attrs |
|---|---|---|
| `member` | profile | profile, preferences, **adherence**, **biomarkers**, **labs**, coach_brief (timeseries stay as attrs — chart endpoints read them directly) |
| `injury` | injuries[] | side, status, severity, since, notes |
| `goal` | goals[] | priority, target_date |
| `workout_session` | workout_history[] | date, completed, duration_min, rpe, exercises |
| `chat_message` | chat_history[] | ts, from, text |
| `joint` / `equipment` (refs) | KG 1 | `ref: movement_kg` — same node id as KG 1 |

### Edge rels

| Rel | From → To | Meaning |
|---|---|---|
| `has_injury` | member → injury | |
| `affects` | injury → joint (KG 1 ref) | **The bridge between the graphs** — safety traversal starts here |
| `has_equipment` | member → equipment (KG 1 ref) | Drives equipment filtering without the coach restating it |
| `has_goal` | member → goal | |
| `performed` | member → workout_session | |
| `chatted` | member → chat_message | |

## How a safety decision traverses (phase 3 preview)

```
member → has_injury → injury(left knee) → affects → joint:knee
  → [part_of⁻¹] → {patella, patellofemoral joint, ACL, …}
  → [stresses⁻¹] → exercises loading any of those     ⇒ exclude/down-rank
condition(PFPS) → contraindicated_for → patterns      ⇒ exclude (plyo) / down-rank (deep flexion)
member → has_equipment → {Dumbbell, Kettlebell, …}
exercise → requires → equipment ∉ available           ⇒ exclude, then find substitutes
```

## Provenance model (PROV-O alignment)

The generation provenance is a hand-rolled record deliberately **aligned to
PROV-O semantics** rather than serialized as RDF — the spec allows a clean
hand-rolled ontology aligned to these concepts, and JSON keeps it renderable
in the UI and queryable in logs. The mapping:

| Our record | PROV-O term | Meaning |
|---|---|---|
| one generation run (`GenerationResult` + `Trace`) | `prov:Activity` | The activity that produced the plan; `TraceEvent`s are its timed steps (`prov:startedAtTime`/`endedAtTime` ≈ `ms`) |
| the generated `WorkoutPlan` | `prov:Entity` | The artifact whose provenance is recorded |
| coach prompt + member context + KG 1 | `prov:Entity` (inputs) | `prov:used` by the activity |
| the LLM composer / the safety filter | `prov:Agent` (`prov:SoftwareAgent`) | `prov:wasAssociatedWith` the activity |
| `SelectedExercise.graph_path` | `prov:wasDerivedFrom` | The KG path justifying inclusion (targets/follows edges + resolved prompt concepts) |
| `RemovedExercise.graph_path` + `reason` | `prov:wasInvalidatedBy` (with justification) | The traversal that excluded the exercise |
| `ResolvedConcept` (query → node, method, confidence) | `prov:wasDerivedFrom` + `prov:value` | How free text became a canonical concept |

Serializing this mapping to actual PROV-O RDF (e.g. for an audit warehouse) is
a mechanical transform of the JSON — left out of the timebox on purpose.

## Ontology decisions — what we pulled, what we left out

- **SNOMED CT (via curated table):** pulled — joint and condition codes as SKOS
  mappings (6 verified `exactMatch` joints; spine/conditions `closeMatch`,
  unverified). It's the clinically meaningful grounding: injuries are the
  safety-critical concepts, and SNOMED codes are what an EHR-adjacent system
  would join on. Left out: live NCI EVS API calls (hermetic demo; the
  `verified` flag marks exactly what a production sync would confirm).
- **SKOS:** pulled — the mapping vocabulary itself (`exactMatch`/`closeMatch`)
  on nodes. It's lightweight and does real work: match strength drives how much
  trust a mapping gets.
- **PROV-O:** pulled as a semantic alignment (table above), not as RDF.
- **OPE (Ontology of Physical Exercises):** consulted, left out of the build.
  The catalog's own taxonomy (19 muscles, 9 joints, 36 patterns, 32 equipment)
  already provides the exercise-domain structure OPE would; importing OPE
  classes would have duplicated those concepts under different IRIs without
  adding a single new safety edge in the timebox. The clean extension is
  SKOS-mapping our `movement_pattern`/`equipment` nodes onto OPE classes the
  same way joints map to SNOMED.
- **COPPER:** consulted, left out. Its personalization/behaviour-change
  concepts (preferences, adherence, goals) are covered structurally by KG 2's
  member nodes; adopting COPPER vocabulary would relabel existing nodes rather
  than enable new reasoning. Revisit if recommendation logic starts using
  behaviour-change techniques explicitly.

Principle applied (per the spec): **a small subset used meaningfully beats
wiring up everything shallowly** — every ontology concept we imported sits on
a traversal path the safety filter or resolver actually walks.
