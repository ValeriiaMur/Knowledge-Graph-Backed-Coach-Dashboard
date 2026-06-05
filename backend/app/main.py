"""FastAPI shell — phase 1. Routes grow per phase; contracts stay typed."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.data_loader import load_exercises, load_member_context
from app.models import Exercise, MemberContext
from app.runtime.generator import generate_workout
from app.runtime.schemas import GenerationResult

load_dotenv()

app = FastAPI(title="Coach Dashboard API")

# Same-origin in production (FastAPI serves the SPA), so CORS is only needed for
# the Vite dev server. Override via ALLOWED_ORIGINS (comma-separated) if needed.
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins if o.strip()],
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


@app.get("/api/graph")
def graph_data() -> dict:
    """KG 1 nodes + links for the visualization panel."""
    from app.graph.movement_kg import build_movement_graph

    g = build_movement_graph()
    # full node attributes (SNOMED mappings, priority tier, …) feed the node
    # detail popover; edge `mode` distinguishes exclude vs down-rank.
    nodes = [{"id": n, **d} for n, d in g.nodes(data=True)]
    links = [
        {"source": u, "target": v, **d}  # d = {"rel": …} (+ "mode" on contraindications)
        for u, v, d in g.edges(data=True)
    ]
    return {"nodes": nodes, "links": links}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.post("/api/copilot/chat")
def copilot_chat(req: ChatRequest) -> dict:
    from app.copilot.agent import run_copilot
    from app.copilot.anthropic_chat import anthropic_chat

    result = run_copilot(req.message, req.session_id, llm=anthropic_chat)
    return {"reply": result.reply, "tool_calls": result.tool_calls, "error": result.error}


@app.post("/api/copilot/chat/stream")
def copilot_chat_stream(req: ChatRequest) -> StreamingResponse:
    """Token-level streaming (SSE): token / tool / done / error events."""
    from app.copilot.agent import run_copilot_stream, sse_format
    from app.copilot.anthropic_chat import anthropic_chat_stream

    def event_source():
        try:
            for event in run_copilot_stream(req.message, req.session_id, anthropic_chat_stream):
                yield sse_format(event)
        except Exception as exc:  # surface as an SSE error frame, not a dropped socket
            yield sse_format({"type": "error", "error": str(exc)})

    return StreamingResponse(event_source(), media_type="text/event-stream")


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


# --- Serve the built frontend (single-service deploy) -----------------------
# In production FastAPI serves the React build so the SPA and API share one
# origin (relative /api/* paths just work, no CORS). In local dev this block is
# skipped — the dist dir doesn't exist and Vite serves the frontend instead.
# FRONTEND_DIST lets the Dockerfile point at an absolute path regardless of how
# the `app` package is installed.
_dist = os.environ.get("FRONTEND_DIST")
_FRONTEND_DIST = Path(_dist) if _dist else Path(__file__).resolve().parents[2] / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        """Serve real files when they exist; otherwise hand back index.html so
        client-side routing works. /api/* never reaches here (matched above)."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
