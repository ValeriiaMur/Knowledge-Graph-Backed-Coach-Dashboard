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
