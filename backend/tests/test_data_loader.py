"""Phase 1 (red-green): the data loader must load and validate both provided JSONs."""

from app.data_loader import load_exercises, load_member_context


def test_loads_all_50_exercises():
    exercises = load_exercises()
    assert len(exercises) == 50


def test_exercise_has_required_graph_fields():
    ex = load_exercises()[0]
    # fields the KG builders (phase 2) will consume
    assert ex.id and ex.name
    assert isinstance(ex.muscle_groups, list)
    assert isinstance(ex.joints_loaded, list)
    assert isinstance(ex.movement_patterns, list)
    assert isinstance(ex.equipment_required, list)
    assert isinstance(ex.priority_tier, int)
    assert isinstance(ex.is_bilateral, bool)


def test_exercise_ids_are_unique():
    exercises = load_exercises()
    ids = [e.id for e in exercises]
    assert len(ids) == len(set(ids))


def test_loads_member_context_sections():
    member = load_member_context()
    # sections KG 2 (phase 2) and the copilot (phase 5) depend on
    assert member.profile
    assert isinstance(member.injuries, list)
    assert isinstance(member.equipment_available, list)
    assert isinstance(member.workout_history, list)
    assert isinstance(member.chat_history, list)
    assert member.adherence is not None
    assert member.biomarkers is not None
    assert member.labs is not None
    assert member.coach_brief is not None


def test_member_has_left_knee_injury_scenario():
    """The spec's seeded scenario must survive loading intact."""
    member = load_member_context()
    blob = str(member.injuries).lower()
    assert "knee" in blob
