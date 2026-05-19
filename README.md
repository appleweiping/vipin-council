# Vipin Council v2.0

A production-grade multi-LLM deliberation system with integrated reasoning algorithms.

## Core Pipeline

```
Query In
    |
    v
[Smart Router] -- classify difficulty (heuristic + LLM)
    |
    +--> Simple (score < 0.25): Fast path (Haiku, instant)
    |
    +--> Moderate (0.25-0.6): Single strong model
    |
    +--> Complex (> 0.6):
            |
            v
        [Task Decomposer] -- break into sub-tasks if multi-part
            |
            v
        [Protocol Engine] -- run selected deliberation protocol
            |
            v
        [Self-Refine] -- generate -> critique -> refine (max 3 rounds)
            |
            v
        Final Answer + Confidence + Dissent + Audit Trail
```

## Integrated Algorithms

| Algorithm | Source | What It Does |
|-----------|--------|-------------|
| Smart Router | RouteLLM (lm-sys) | Classifies difficulty, routes simple queries to fast models |
| Self-Refine | Madaan et al. 2023 | Iterative critique-and-improve loop (2-3 rounds) |
| Tree of Thoughts | Yao et al. 2023 | Beam search over candidates with multi-model voting |
| Task Decomposer | CrewAI pattern | Breaks complex queries into specialist sub-tasks |
| Peer Review | Karpathy llm-council | Anonymized cross-evaluation between models |
| Consensus Loop | Novel | Iterative convergence with agreement threshold |

## 6 Deliberation Protocols

| Protocol | Best For | How It Works |
|----------|----------|-------------|
| `council` | Open questions | All answer -> peer review -> chairman synthesis |
| `debate` | Controversial topics | Pro vs con -> rebuttals -> judge verdict |
| `redteam` | Testing ideas | Defend -> attack -> improve iteratively |
| `consensus` | Team alignment | Rounds until agreement threshold met |
| `specialist` | Domain expertise | Classify -> route to expert -> verify |
| `tournament` | Best single answer | Bracket elimination, head-to-head |

## 6-Agent Lineup

| Agent | Model | Role | Strengths |
|-------|-------|------|-----------|
| Opus | Claude 4.7 | Architect + Chairman | Complex reasoning, paper writing |
| Codex | GPT-5.5 | Coordinator | Parallel execution, fast iteration |
| OpenCode | Claude 4.7 | Implementer | Code, testing, docs |
| Sonnet | Claude 4.6 | Reviewer | Quality gate, verification |
| Haiku | Claude 4.5 | Speedster | Pre-screening, fast triage |
| DeepSeek | DeepSeek V4 | Bulk Worker | Translation, long generation |

## Quick Start

```bash
pip install -e .
cp .env.example .env  # Add your OPENROUTER_API_KEY
uvicorn backend.main:app --reload --port 8000
```

## API

```bash
# Simple query (auto-routed)
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a monad?", "protocol": "council"}'

# Debate mode
curl -X POST http://localhost:8000/api/query \
  -d '{"query": "Should startups use microservices?", "protocol": "debate"}'

# Red team your idea
curl -X POST http://localhost:8000/api/query \
  -d '{"query": "My plan is to build X", "protocol": "redteam"}'
```

## Response Format

```json
{
  "session_id": "uuid",
  "protocol": "council",
  "stages": [...],
  "final_answer": "The synthesized, refined answer",
  "confidence": 0.87,
  "dissent": ["Model X disagrees because..."],
  "audit_trail": [
    {"step": "routing", "tier": "full_council", "difficulty": 0.72},
    {"step": "decompose", "subtask_count": 3},
    {"step": "protocol", "name": "council", "stages": 3},
    {"step": "refine", "iterations": 2, "final_score": 8.5}
  ]
}
```

## Architecture

```
vipin-council/
├── backend/
│   ├── main.py                  # FastAPI endpoints
│   ├── config.py                # 6-agent configuration
│   ├── engine/                  # Core algorithms
│   │   ├── smart_router.py      # RouteLLM-style difficulty routing
│   │   ├── self_refine.py       # Generate -> critique -> refine loop
│   │   ├── tree_of_thoughts.py  # Beam search with voting
│   │   └── task_decomposer.py   # CrewAI-style task breakdown
│   ├── council/
│   │   ├── orchestrator.py      # Pipeline: route -> decompose -> protocol -> refine
│   │   └── session.py           # Session data model
│   ├── protocols/               # 6 deliberation protocols
│   ├── providers/
│   │   └── router.py            # OpenRouter API client
│   └── memory/
│       └── tracker.py           # Cross-session performance memory
├── data/sessions/               # Saved deliberation sessions
├── pyproject.toml
└── .env.example
```

## vs. Other Projects

| Feature | llm-council | AutoGen | CrewAI | vipin-council |
|---------|-------------|---------|--------|---------------|
| Deliberation protocols | 1 | 0 | 0 | **6** |
| Smart routing | No | No | No | **Yes** |
| Self-refine loop | No | No | No | **Yes (3 rounds)** |
| Tree of Thoughts | No | No | No | **Yes (beam=5)** |
| Task decomposition | No | Yes | Yes | **Yes** |
| Confidence scoring | No | No | No | **Yes** |
| Dissent preservation | No | No | No | **Yes** |
| Cross-session memory | No | No | No | **Yes** |
| Audit trail | No | Partial | Partial | **Full** |

## License

MIT
