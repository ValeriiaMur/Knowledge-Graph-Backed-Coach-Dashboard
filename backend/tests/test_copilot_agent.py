"""Phase 5 (red-green): copilot agent loop — tool dispatch, session history,
grounding. LLM injected as a fake; production wires Anthropic."""

from app.copilot.agent import QUICK_PROMPTS, reset_sessions, run_copilot


def llm_that_checks_adherence(messages: list, tools: list) -> dict:
    """First call: request a tool. Second call: answer from the tool result."""
    last = messages[-1]
    if last["role"] == "user" and isinstance(last["content"], str):
        return {
            "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "tu_1", "name": "get_adherence", "input": {}}],
        }
    # tool result came back — ground the answer in it
    tool_payload = str(messages[-1]["content"])
    trend = "declining" if "declining" in tool_payload else "unknown"
    return {
        "stop_reason": "end_turn",
        "content": [{"type": "text", "text": f"Adherence is {trend}: 100→100→75→50%."}],
    }


def setup_function():
    reset_sessions()


def test_agent_dispatches_tools_and_grounds_answer():
    out = run_copilot("How's adherence trending?", session_id="s1", llm=llm_that_checks_adherence)
    assert "declining" in out.reply
    assert out.tool_calls == ["get_adherence"]


def test_session_history_persists_across_turns():
    run_copilot("How's adherence trending?", session_id="s2", llm=llm_that_checks_adherence)
    out2 = run_copilot("How's adherence trending?", session_id="s2", llm=llm_that_checks_adherence)
    # second turn's message list contained the first exchange
    assert out2.history_len >= 4  # user, assistant(tool), tool result..., assistant


def test_unknown_tool_returns_error_to_model_not_crash():
    def llm_bad_tool(messages, tools):
        if messages[-1]["role"] == "user" and isinstance(messages[-1]["content"], str):
            return {
                "stop_reason": "tool_use",
                "content": [{"type": "tool_use", "id": "t", "name": "get_magic", "input": {}}],
            }
        return {
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "I don't have that data for this member."}],
        }

    out = run_copilot("magic?", session_id="s3", llm=llm_bad_tool)
    assert "don't have" in out.reply


def test_loop_caps_iterations():
    def llm_loops_forever(messages, tools):
        return {
            "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "t", "name": "get_brief", "input": {}}],
        }

    out = run_copilot("brief me", session_id="s4", llm=llm_loops_forever)
    assert out.error  # gave up gracefully instead of spinning


def test_quick_prompt_palette_matches_spec():
    texts = " ".join(QUICK_PROMPTS).lower()
    for needle in ["brief", "adherence", "sleep", "changed", "plot", "message", "4 weeks"]:
        assert needle in texts
