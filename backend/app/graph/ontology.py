"""Curated ontology layer — hand-rolled, aligned to SNOMED CT / OPE via SKOS-style mappings.

Decision (PRESEARCH §6/§7): a small curated table used meaningfully beats parsing full OWL.
Codes marked verified=False must be confirmed against NCI EVS before any production claim.
"""

from typing import TypedDict


class SkosMapping(TypedDict):
    scheme: str
    code: str | None
    label: str
    match: str  # skos:exactMatch | skos:closeMatch
    verified: bool


# --- Anatomy hierarchy: substructure -> part_of -> joint -------------------
# Why these: injury filtering must expand a joint to its sub-structures
# (spec: "so sub-structures count too"). Kept to clinically common structures
# that exercise contraindications actually reference.
ANATOMY_SUBSTRUCTURES: dict[str, list[str]] = {
    "knee": ["patellofemoral joint", "patella", "patellar tendon", "acl", "meniscus"],
    "shoulder": ["glenohumeral joint", "rotator cuff complex", "acromioclavicular joint"],
    "ankle": ["achilles tendon", "subtalar joint"],
    "hip": ["hip labrum"],
    "lumbar spine": ["lumbar intervertebral discs"],
    "elbow": ["common extensor tendon"],
    "wrist": ["carpal tunnel"],
}

# --- SKOS mappings: our canonical joints -> SNOMED CT ----------------------
JOINT_MAPPINGS: dict[str, list[SkosMapping]] = {
    "knee": [
        {
            "scheme": "snomedct",
            "code": "49076000",
            "label": "Knee joint structure",
            "match": "skos:exactMatch",
            "verified": True,
        }
    ],
    "shoulder": [
        {
            "scheme": "snomedct",
            "code": "16982005",
            "label": "Shoulder joint structure",
            "match": "skos:exactMatch",
            "verified": True,
        }
    ],
    "hip": [
        {
            "scheme": "snomedct",
            "code": "24136001",
            "label": "Hip joint structure",
            "match": "skos:exactMatch",
            "verified": True,
        }
    ],
    "elbow": [
        {
            "scheme": "snomedct",
            "code": "16953009",
            "label": "Elbow joint structure",
            "match": "skos:exactMatch",
            "verified": True,
        }
    ],
    "wrist": [
        {
            "scheme": "snomedct",
            "code": "74670003",
            "label": "Wrist joint structure",
            "match": "skos:exactMatch",
            "verified": True,
        }
    ],
    "ankle": [
        {
            "scheme": "snomedct",
            "code": "70258002",
            "label": "Ankle joint structure",
            "match": "skos:exactMatch",
            "verified": True,
        }
    ],
    "cervical spine": [
        {
            "scheme": "snomedct",
            "code": None,
            "label": "Cervical vertebral column structure",
            "match": "skos:closeMatch",
            "verified": False,
        }
    ],
    "thoracic spine": [
        {
            "scheme": "snomedct",
            "code": None,
            "label": "Thoracic vertebral column structure",
            "match": "skos:closeMatch",
            "verified": False,
        }
    ],
    "lumbar spine": [
        {
            "scheme": "snomedct",
            "code": None,
            "label": "Lumbar vertebral column structure",
            "match": "skos:closeMatch",
            "verified": False,
        }
    ],
}

# --- Conditions: located_in a structure, contraindicated_for patterns ------
# Seeded from the dataset's injury notes ("avoid deep knee flexion under load
# and plyometrics"). mode: "exclude" = hard filter, "down_rank" = caution.
CONDITIONS: dict[str, dict] = {
    "patellofemoral pain syndrome": {
        "located_in": ["patellofemoral joint"],
        "contraindicated_patterns": {
            "cardio - plyometric": "exclude",
            "lower push - squat": "down_rank",
            "lower push - lunge": "down_rank",
            "lower push - split squat": "down_rank",
        },
        "skos_mappings": [
            {
                "scheme": "snomedct",
                "code": None,
                "label": "Patellofemoral pain syndrome — verify via NCI EVS",
                "match": "skos:closeMatch",
                "verified": False,
            }
        ],
    },
}

# Free-text region aliases the resolver (phase 3) will also use.
REGION_ALIASES: dict[str, str] = {
    "left knee": "knee",
    "right knee": "knee",
    "lower back": "lumbar spine",
    "bad lower back": "lumbar spine",
    "neck": "cervical spine",
}
