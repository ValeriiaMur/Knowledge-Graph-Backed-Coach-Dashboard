"""Load and validate the provided synthetic datasets (data/ at repo root)."""

import json
from functools import lru_cache
from pathlib import Path

from app.models import Exercise, MemberContext

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache(maxsize=1)
def load_exercises() -> list[Exercise]:
    raw = json.loads((DATA_DIR / "exercises.json").read_text())
    return [Exercise.model_validate(item) for item in raw]


@lru_cache(maxsize=1)
def load_member_context() -> MemberContext:
    raw = json.loads((DATA_DIR / "member-context.json").read_text())
    return MemberContext.model_validate(raw)
