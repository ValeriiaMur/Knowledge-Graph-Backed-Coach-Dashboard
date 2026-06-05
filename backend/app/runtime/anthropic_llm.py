"""Production plan composer — Claude tool use. The model receives ONLY the
safety-allowed candidates (plus removal reasons for context) and must answer
via the submit_plan tool, giving us schema-shaped output to validate."""

import json
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

SUBMIT_PLAN_TOOL = {
    "name": "submit_plan",
    "description": "Submit the final structured workout plan.",
    "input_schema": {
        "type": "object",
        "properties": {
            section: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "exercise": {"type": "string", "description": "candidate node_id"},
                        "sets": {"type": "integer"},
                        "reps": {"type": "integer"},
                        "duration_sec": {"type": "integer"},
                        "rest_sec": {"type": "integer"},
                    },
                    "required": ["exercise", "sets", "rest_sec"],
                },
            }
            for section in ("warmup", "main", "cooldown")
        },
        "required": ["warmup", "main", "cooldown"],
    },
}

SYSTEM = """You are a strength coach's planning assistant. Compose a workout from the
provided candidate exercises ONLY — reference them by node_id. Respect the time budget,
prefer lower priority_tier, use down_ranked candidates sparingly and never in warmup.
Structure: brief warmup, focused main block, short cooldown. Call submit_plan exactly once."""


@lru_cache(maxsize=1)
def _client():
    import anthropic

    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY


def anthropic_compose(payload: dict) -> dict:
    response = _client().messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM,
        tools=[SUBMIT_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "submit_plan"},
        messages=[{"role": "user", "content": json.dumps(payload)}],
    )
    logger.info(
        "trace step=anthropic_compose tokens_in=%s tokens_out=%s",
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_plan":
            return block.input
    raise ValueError("Claude did not call submit_plan")
