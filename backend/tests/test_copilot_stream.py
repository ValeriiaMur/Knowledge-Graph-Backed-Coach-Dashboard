"""Red-green: streaming copilot loop — token deltas, tool events, final done."""

from app.copilot.agent import reset_sessions, run_copilot_stream, sse_format


def fake_stream_factory(turns):
    """Each turn: (token_texts, final_event). Pops one turn per LLM call."""
    calls = list(turns)

    def fake_stream(messages, tools):
        tokens, final = calls.pop(0)
        for t in tokens:
            yield {"type": "token", "text": t}
        yield final

    return fake_stream


def test_stream_yields_tokens_then_done_without_tools():
    reset_sessions()
    llm = fake_stream_factory(
        [
            (
                ["Adherence ", "is ", "declining."],
                {
                    "type": "final",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": "Adherence is declining."}],
                },
            )
        ]
    )
    events = list(run_copilot_stream("how is adherence?", "s1", llm_stream=llm))
    kinds = [e["type"] for e in events]
    assert kinds == ["token", "token", "token", "done"]
    assert events[-1]["reply"] == "Adherence is declining."
    assert events[-1]["tool_calls"] == []


def test_stream_emits_tool_events_between_token_runs():
    reset_sessions()
    llm = fake_stream_factory(
        [
            (
                [],
                {
                    "type": "final",
                    "stop_reason": "tool_use",
                    "content": [
                        {"type": "tool_use", "id": "t1", "name": "get_adherence", "input": {}}
                    ],
                },
            ),
            (
                ["Weekly ", "completion ", "fell."],
                {
                    "type": "final",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": "Weekly completion fell."}],
                },
            ),
        ]
    )
    events = list(run_copilot_stream("trend?", "s2", llm_stream=llm))
    kinds = [e["type"] for e in events]
    assert kinds == ["tool", "token", "token", "token", "done"]
    assert events[0]["name"] == "get_adherence"
    assert events[-1]["tool_calls"] == ["get_adherence"]


def test_stream_unknown_tool_is_resilient():
    reset_sessions()
    llm = fake_stream_factory(
        [
            (
                [],
                {
                    "type": "final",
                    "stop_reason": "tool_use",
                    "content": [{"type": "tool_use", "id": "t1", "name": "nope", "input": {}}],
                },
            ),
            (
                ["Not in this member's context."],
                {
                    "type": "final",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": "Not in this member's context."}],
                },
            ),
        ]
    )
    events = list(run_copilot_stream("?", "s3", llm_stream=llm))
    assert events[-1]["type"] == "done"
    assert events[-1]["tool_calls"] == ["nope"]


def test_stream_caps_tool_iterations():
    reset_sessions()
    endless = (
        [],
        {
            "type": "final",
            "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "t", "name": "get_brief", "input": {}}],
        },
    )
    llm = fake_stream_factory([endless] * 10)
    events = list(run_copilot_stream("loop", "s4", llm_stream=llm))
    assert events[-1]["type"] == "error"
    assert events[-1]["error"] == "max_tool_iterations"


def test_sse_format_is_valid_event_stream_frame():
    frame = sse_format({"type": "token", "text": "hi"})
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    assert '"token"' in frame
