"""Anthropic adapter for the copilot loop — normalizes SDK responses to the
plain-dict shape the agent consumes (so the loop stays testable offline)."""

import logging
import os
from functools import lru_cache

from app.copilot.agent import SYSTEM

logger = logging.getLogger(__name__)

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


@lru_cache(maxsize=1)
def _client():
    import anthropic

    return anthropic.Anthropic()


def anthropic_chat(messages: list, tools: list) -> dict:
    response = _client().messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM,
        tools=tools,
        messages=messages,
    )
    logger.info(
        "trace step=copilot_llm tokens_in=%s tokens_out=%s stop=%s",
        response.usage.input_tokens,
        response.usage.output_tokens,
        response.stop_reason,
    )
    content = []
    for block in response.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append(
                {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
            )
    return {"stop_reason": response.stop_reason, "content": content}
