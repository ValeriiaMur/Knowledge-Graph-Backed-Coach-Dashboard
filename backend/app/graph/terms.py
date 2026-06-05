"""Canonical node-kind and edge-relation names — the graph's vocabulary in one place.

A bare string literal at a call site fails *silently* on a typo: the edge simply
never matches a traversal filter, which is a dangerous failure mode for a safety
graph (a contraindication that quietly stops applying). Referencing these
constants instead turns a typo into an immediate NameError, and gives one
authoritative list of the ontology's vocabulary.
"""


class Kind:
    """`kind` attribute on every node."""

    MUSCLE = "muscle"
    JOINT = "joint"
    EQUIPMENT = "equipment"
    MOVEMENT_PATTERN = "movement_pattern"
    EXERCISE = "exercise"
    SUBSTRUCTURE = "substructure"
    CONDITION = "condition"
    # KG 2 (member context)
    MEMBER = "member"
    INJURY = "injury"
    GOAL = "goal"
    WORKOUT_SESSION = "workout_session"
    CHAT_MESSAGE = "chat_message"


class Rel:
    """`rel` attribute on every edge."""

    # KG 1 (movement / clinical)
    PART_OF = "part_of"
    LOCATED_IN = "located_in"
    CONTRAINDICATED_FOR = "contraindicated_for"
    TARGETS = "targets"
    STRESSES = "stresses"
    REQUIRES = "requires"
    FOLLOWS = "follows"
    # KG 2 (member context)
    HAS_INJURY = "has_injury"
    AFFECTS = "affects"
    HAS_EQUIPMENT = "has_equipment"
    HAS_GOAL = "has_goal"
    PERFORMED = "performed"
    CHATTED = "chatted"
