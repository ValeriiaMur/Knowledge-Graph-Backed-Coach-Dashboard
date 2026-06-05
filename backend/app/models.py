"""Typed contracts for the provided datasets. Loose where the spec is open
(dict sections we only render/retrieve), strict where the KG builders consume fields."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class Exercise(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    muscle_groups: list[str]
    joints_loaded: list[str]
    movement_patterns: list[str]
    equipment_required: list[str]
    priority_tier: int
    is_bilateral: bool
    bilateral_pair_id: str | None = None
    side: str | None = None
    is_reps: bool | None = None
    is_duration: bool | None = None
    supports_weight: bool | None = None
    estimated_rep_duration: float | None = None


class MemberContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    profile: dict[str, Any]
    goals: list[Any] | dict[str, Any]
    preferences: dict[str, Any] | list[Any]
    equipment_available: list[Any]
    injuries: list[Any]
    workout_history: list[Any]
    adherence: dict[str, Any] | list[Any]
    biomarkers: dict[str, Any] | list[Any]
    labs: dict[str, Any]
    chat_history: list[Any]
    coach_brief: dict[str, Any]
