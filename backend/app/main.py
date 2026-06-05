"""FastAPI shell — phase 1. Routes grow per phase; contracts stay typed."""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.data_loader import load_exercises, load_member_context
from app.models import Exercise, MemberContext
from app.runtime.generator import generate_workout
from app.runtime.schemas import GenerationResult

load_dotenv()

app = FastAPI(title="Coach Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/exercises")
def exercises() -> list[Exercise]:
    return load_exercises()


@app.get("/api/member")
def member() -> MemberContext:
    return load_member_context()


class GenerateRequest(BaseModel):
    prompt: str
    minutes: int = 30
    use_member_context: bool = True


@app.post("/api/generate")
def generate(req: GenerateRequest) -> GenerationResult:
    from app.runtime.anthropic_llm import anthropic_compose

    return generate_workout(
        req.prompt, req.minutes, llm=anthropic_compose, use_member_context=req.use_member_context
    )
