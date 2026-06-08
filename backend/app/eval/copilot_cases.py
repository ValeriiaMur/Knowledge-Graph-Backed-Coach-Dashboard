"""Copilot answer-quality eval set — questions + ground-truth references.

Used by the Ragas lane (`app/eval/ragas_eval.py`), NOT the deterministic gate.
References are hand-written from the synthetic member (Jordan Rivera) in
`data/member-context.json`; they are the "correct answer" Ragas scores against
for reference-based metrics (context precision/recall). Faithfulness and answer
relevancy don't need them, but having them makes the lane more rigorous.

The last case is a deliberate grounding probe: the metric isn't in this member's
context, so a faithful copilot must decline rather than invent a number.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CopilotCase:
    question: str
    reference: str  # ground-truth answer derived from member-context.json


CASES: list[CopilotCase] = [
    CopilotCase(
        question="Is she at risk of churning?",
        reference=(
            "Yes — churn risk is elevated. Weekly adherence fell from 100% to 50% over "
            "two weeks, she skipped a session citing fatigue/work, and her login "
            "frequency is down versus the prior month."
        ),
    ),
    CopilotCase(
        question="How is her adherence trending?",
        reference=(
            "Adherence is declining: weekly completion went 100%, 100%, 75%, 50% over "
            "the last four weeks (weeks of 05-12, 05-19, 05-26, and 06-02)."
        ),
    ),
    CopilotCase(
        question="How many hours has she been sleeping this week?",
        reference=(
            "Over the last seven days her sleep was 6.1, 5.4, 7.2, 6.0, 5.1, 7.8, and "
            "6.3 hours — averaging roughly 6.3 hours per night, below her 7-hour goal."
        ),
    ),
    CopilotCase(
        question="Does she have any injuries I should know about?",
        reference=(
            "Yes — a recovering left-knee injury (patellofemoral pain after a hiking "
            "trip), mild severity, since 2026-05-10. She's cleared for low-impact "
            "loading but should avoid deep knee flexion under load and plyometrics."
        ),
    ),
    CopilotCase(
        question="What equipment does she have at home?",
        reference=(
            "Dumbbell, Kettlebell, Yoga Mat, a Resistance Band (loop), and a Flat "
            "Bench. No barbell."
        ),
    ),
    CopilotCase(
        question="What are her goals?",
        reference=(
            "Build lower-body strength, return to pain-free squatting after the "
            "left-knee flare-up, and average 7+ hours of sleep on weeknights."
        ),
    ),
    # Grounding probe: step count is NOT in this member's context. A faithful
    # copilot must say so rather than fabricate a figure.
    CopilotCase(
        question="What's her average daily step count?",
        reference=(
            "Daily step count is not in this member's context, so it can't be "
            "answered from the available data."
        ),
    ),
]
