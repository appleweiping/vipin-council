"""FastAPI backend for vipin-council."""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import CouncilConfig
from .council.orchestrator import Orchestrator
from .council.session import Session

app = FastAPI(title="Vipin Council", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

config = CouncilConfig()
orchestrator = Orchestrator(config)

DATA_DIR = Path(__file__).parent.parent / "data" / "sessions"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class QueryRequest(BaseModel):
    query: str
    protocol: str = "council"  # council, debate, redteam, consensus, specialist, tournament
    context: str | None = None


class QueryResponse(BaseModel):
    session_id: str
    protocol: str
    stages: list[dict]
    final_answer: str
    confidence: float
    dissent: list[str]
    audit_trail: list[dict]


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "models": len(config.models)}


@app.get("/api/models")
async def list_models():
    return [{"id": m.id, "name": m.name, "role": m.role, "strengths": m.strengths} for m in config.models]


@app.get("/api/protocols")
async def list_protocols():
    return [
        {"id": "council", "name": "Council", "description": "All models answer, peer review, chairman synthesizes"},
        {"id": "debate", "name": "Debate", "description": "Two sides argue opposing positions, judge decides"},
        {"id": "redteam", "name": "Red Team", "description": "One model attacks, others defend and find weaknesses"},
        {"id": "consensus", "name": "Consensus", "description": "Iterative rounds until agreement threshold met"},
        {"id": "specialist", "name": "Specialist", "description": "Route to domain expert, others verify"},
        {"id": "tournament", "name": "Tournament", "description": "Bracket elimination, best answer wins"},
    ]


@app.post("/api/query", response_model=QueryResponse)
async def submit_query(req: QueryRequest):
    session = Session(
        id=str(uuid.uuid4()),
        query=req.query,
        protocol=req.protocol,
        context=req.context,
        created_at=datetime.utcnow().isoformat(),
    )
    result = await orchestrator.run(session)

    # Save session
    session_path = DATA_DIR / f"{session.id}.json"
    session_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    return QueryResponse(
        session_id=session.id,
        protocol=req.protocol,
        stages=result.stages,
        final_answer=result.final_answer,
        confidence=result.confidence,
        dissent=result.dissent,
        audit_trail=result.audit_trail,
    )


@app.get("/api/sessions")
async def list_sessions():
    sessions = []
    for f in sorted(DATA_DIR.glob("*.json"), reverse=True)[:50]:
        data = json.loads(f.read_text())
        sessions.append({"id": data["id"], "query": data["query"][:100], "protocol": data["protocol"], "created_at": data["created_at"]})
    return sessions


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    path = DATA_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(404, "Session not found")
    return json.loads(path.read_text())
