"""Ragas lane — answer-quality eval for the copilot's NL layer.

WHY THIS IS SEPARATE FROM `make eval`:
The deterministic core (resolver, safety filter, generator structure) is graded
by exact-match assertions in `app/eval/run.py` — that must stay deterministic and
fast. THIS lane uses an LLM judge, so it is non-deterministic, costs tokens, and
needs network. It targets the one thing the gate can't: whether the copilot's
*natural-language answer* is faithful to what it retrieved, relevant to the
question, and backed by the right context. Run it periodically, never in the
fast CI gate.

HOW CONTEXTS ARE CAPTURED:
The copilot "retrieves" via tool calls (KG 2). After a run, the session history
holds `tool_result` blocks — their JSON payloads ARE the retrieved contexts.
We pull them straight from the agent's session store; no copilot code changes.

JUDGE STACK: reuses the project's own models — Anthropic (ANTHROPIC_MODEL) as the
judge LLM, Voyage as the embeddings model — so no new credentials are needed.

Run:  make eval-ragas   (or  python -m app.eval.ragas_eval)
"""

import os
import sys

from app.eval.copilot_cases import CASES

# Soft pass thresholds (0..1). Tunable; LLM-judge variance means treat these as
# guidance, not a hard contract. Exit code is non-zero only if a mean dips below.
THRESHOLDS = {
    "faithfulness": 0.70,
    "answer_relevancy": 0.70,
    "context_precision": 0.60,
}


def _collect_contexts(session_id: str) -> list[str]:
    """Pull every tool_result payload from the agent session = retrieved contexts."""
    from app.copilot.agent import _sessions

    contexts: list[str] = []
    for msg in _sessions.get(session_id, []):
        content = msg.get("content")
        if msg.get("role") == "user" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    contexts.append(str(block.get("content", "")))
    return contexts


def _build_samples() -> list[dict]:
    """Run the live copilot once per case; assemble Ragas evaluation rows."""
    from app.copilot.agent import reset_sessions, run_copilot
    from app.copilot.anthropic_chat import anthropic_chat

    samples: list[dict] = []
    for i, case in enumerate(CASES):
        reset_sessions()
        sid = f"ragas_{i}"
        result = run_copilot(case.question, sid, llm=anthropic_chat)
        contexts = _collect_contexts(sid) or ["(no context retrieved)"]
        print(
            f"  · case {i + 1}/{len(CASES)}: {case.question!r} "
            f"→ {len(contexts)} context(s), {len(result.tool_calls)} tool call(s)"
        )
        samples.append(
            {
                "user_input": case.question,
                "response": result.reply,
                "retrieved_contexts": contexts,
                "reference": case.reference,
            }
        )
    return samples


def _judges():
    """Wrap the project's Anthropic + Voyage models as Ragas judge/embeddings."""
    from langchain_anthropic import ChatAnthropic
    from langchain_voyageai import VoyageAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    voyage_model = os.environ.get("VOYAGE_MODEL", "voyage-3")
    llm = LangchainLLMWrapper(ChatAnthropic(model=model, max_tokens=2000, temperature=0))
    embeddings = LangchainEmbeddingsWrapper(VoyageAIEmbeddings(model=voyage_model))
    return llm, embeddings


def _metrics():
    """Faithfulness + answer relevancy + context precision, tolerant of Ragas
    version renames (AnswerRelevancy→ResponseRelevancy, etc.)."""
    from ragas import metrics as m

    faithfulness = m.Faithfulness()
    relevancy = (getattr(m, "ResponseRelevancy", None) or m.AnswerRelevancy)()
    precision_cls = getattr(m, "LLMContextPrecisionWithReference", None) or getattr(
        m, "ContextPrecision", None
    )
    out = [faithfulness, relevancy]
    if precision_cls is not None:
        out.append(precision_cls())
    return out


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ragas-eval: SKIPPED — ANTHROPIC_API_KEY not set (judge + copilot need it).")
        return 0
    if not os.environ.get("VOYAGE_API_KEY"):
        print("ragas-eval: SKIPPED — VOYAGE_API_KEY not set (embeddings judge needs it).")
        return 0

    try:
        import ragas  # noqa: F401
    except ModuleNotFoundError:
        print(
            "ragas-eval: SKIPPED — optional deps not installed. From backend/ run:\n"
            "  python3 -m pip install -e '.[eval]'"
        )
        return 0

    try:
        from ragas import EvaluationDataset, evaluate
    except Exception as exc:  # ragas present but its import chain is broken
        print(
            "ragas-eval: SKIPPED — ragas is installed but failed to import "
            f"(likely a langchain version mismatch):\n  {type(exc).__name__}: {exc}\n"
            "Fix by reinstalling the pinned matrix from backend/:\n"
            "  python3 -m pip install -e '.[eval]'"
        )
        return 0

    print(f"ragas-eval: running copilot over {len(CASES)} cases…")
    samples = _build_samples()
    dataset = EvaluationDataset.from_list(samples)

    llm, embeddings = _judges()
    print("ragas-eval: scoring with Anthropic judge + Voyage embeddings…")
    report = evaluate(dataset, metrics=_metrics(), llm=llm, embeddings=embeddings)

    df = report.to_pandas()
    print("\n=== Ragas scores (per metric mean) ===")
    failures: list[str] = []
    for col, floor in THRESHOLDS.items():
        if col not in df.columns:
            continue
        mean = float(df[col].mean())
        flag = "ok" if mean >= floor else "LOW"
        print(f"  {col:18s} {mean:.3f}  (floor {floor:.2f}) [{flag}]")
        if mean < floor:
            failures.append(f"{col} {mean:.3f} < {floor:.2f}")

    # Surface the weakest individual answers for inspection.
    print("\n=== Per-case (lowest faithfulness first) ===")
    score_cols = [c for c in df.columns if c in THRESHOLDS]
    sort_col = "faithfulness" if "faithfulness" in df.columns else score_cols[0]
    for _, row in df.sort_values(sort_col).iterrows():
        scores = " ".join(f"{c}={row[c]:.2f}" for c in score_cols)
        print(f"  {scores}  | {str(row['user_input'])[:50]}")

    if failures:
        print("\nragas-eval: BELOW THRESHOLD — " + "; ".join(failures))
        return 1
    print("\nragas-eval: all metrics above thresholds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
