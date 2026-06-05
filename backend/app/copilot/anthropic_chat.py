"""Anthropic adapter for the copilot loop — normalizes SDK responses to the
plain-dict shape the agent consumes (so the loop stays testable offline)."""

import logging
import os
from collections.abc import Iterator
from functools import lru_cache

from app.copilot.agent import SYSTEM

logger = logging.getLogger(__name__)

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


@lru_cache(maxsize=1)
def _client():
    import anthropic

    return anthropic.Anthropic()


def _normalize_content(response) -> list[dict]:
    content: list[dict] = []
    for block in response.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append(
                {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
            )
    return content


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
    return {"stop_reason": response.stop_reason, "content": _normalize_content(response)}


def anthropic_chat_stream(messages: list, tools: list) -> Iterator[dict]:
    """Streaming adapter (agent.StreamLlmFn contract): yields token deltas as
    they arrive, then the same normalized final shape anthropic_chat returns."""
    with _client().messages.stream(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM,
        tools=tools,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield {"type": "token", "text": text}
        response = stream.get_final_message()

    logger.info(
        "trace step=copilot_llm_stream tokens_in=%s tokens_out=%s stop=%s",
        response.usage.input_tokens,
        response.usage.output_tokens,
        response.stop_reason,
    )
    yield {
        "type": "final",
        "stop_reason": response.stop_reason,
        "content": _normalize_content(response),
    }
