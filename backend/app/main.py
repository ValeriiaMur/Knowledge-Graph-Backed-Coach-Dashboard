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


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.post("/api/copilot/chat")
def copilot_chat(req: ChatRequest) -> dict:
    from app.copilot.agent import run_copilot
    from app.copilot.anthropic_chat import anthropic_chat

    result = run_copilot(req.message, req.session_id, llm=anthropic_chat)
    return {"reply": result.reply, "tool_calls": result.tool_calls, "error": result.error}


@app.get("/api/copilot/quick-prompts")
def quick_prompts() -> list[str]:
    from app.copilot.agent import QUICK_PROMPTS

    return QUICK_PROMPTS


@app.get("/api/copilot/chat-history")
def member_chat_history() -> list[dict]:
    from app.copilot.retrieval import get_chat_history

    return get_chat_history()


@app.get("/api/member/timeseries/{metric}")
def timeseries(metric: str) -> dict:
    from app.copilot.retrieval import get_timeseries

    return get_timeseries(metric)


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
