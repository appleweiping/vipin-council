# Vipin Council

A multi-LLM deliberation system that goes beyond simple "ask multiple models and pick the best." Instead of one protocol, Vipin Council implements **6 distinct deliberation strategies**, each suited to different types of questions.

## Why This Exists

Karpathy's `llm-council` showed that asking multiple LLMs and having them review each other produces better answers. Vipin Council takes this further:

| Feature | llm-council | vipin-council |
|---------|-------------|---------------|
| Protocols | 1 (council) | 6 (council, debate, red-team, consensus, specialist, tournament) |
| Role specialization | No | Yes (architect, critic, researcher, practitioner) |
| Cross-session memory | No | Yes (tracks which models excel at what) |
| Confidence scoring | No | Yes (calibrated per-answer confidence) |
| Dissent tracking | No | Yes (preserves minority opinions) |
| Audit trail | No | Yes (full decision provenance) |
| Structured output | No | Yes (JSON schema responses) |

## Protocols

### Council (Classic)
All models answer independently. Each reviews the others (anonymized). A Chairman synthesizes the best answer.

### Debate
Two models take opposing sides. They deliver opening statements, then rebuttals. A third model judges.

### Red Team
One model proposes an answer. Another attacks it, finding weaknesses. The original model improves based on criticism. Repeat until robust.

### Consensus
All models answer. They see each other's responses and revise. Repeat until agreement threshold is met or max rounds reached.

### Specialist
The system classifies the query domain, routes to the model with the best track record in that domain, then other models verify the specialist's answer.

### Tournament
Models are paired in brackets. Each pair's answers are judged head-to-head. Winners advance. Final winner's answer is the output.

## Quick Start

```bash
# Install
pip install -e .

# Set API key
cp .env.example .env
# Edit .env with your OpenRouter API key

# Run backend
uvicorn backend.main:app --reload --port 8000

# Run frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## API

```bash
# Health check
curl http://localhost:8000/api/health

# List models
curl http://localhost:8000/api/models

# List protocols
curl http://localhost:8000/api/protocols

# Submit query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the best approach to distributed consensus?", "protocol": "debate"}'
```

## Configuration

Edit `backend/config.py` to customize:
- Which models sit on the council
- Which model is Chairman
- Default protocol
- Confidence thresholds
- Max consensus rounds

## Architecture

```
vipin-council/
├── backend/
│   ├── main.py              # FastAPI endpoints
│   ├── config.py            # Model and council configuration
│   ├── council/
│   │   ├── orchestrator.py  # Routes to protocols
│   │   └── session.py       # Session data model
│   ├── protocols/
│   │   ├── base.py          # Protocol interface
│   │   ├── council_protocol.py
│   │   ├── debate_protocol.py
│   │   ├── redteam_protocol.py
│   │   ├── consensus_protocol.py
│   │   ├── specialist_protocol.py
│   │   └── tournament_protocol.py
│   ├── providers/
│   │   └── router.py        # OpenRouter API client
│   └── memory/
│       └── tracker.py       # Performance tracking
├── frontend/                 # React UI
├── data/
│   └── sessions/            # Saved deliberation sessions
├── pyproject.toml
└── .env.example
```

## Design Principles

1. **Preserve dissent** — Minority opinions are recorded, not discarded
2. **Audit everything** — Every model's contribution is traceable
3. **Learn over time** — The system remembers which models excel at what
4. **Match protocol to problem** — Different questions need different deliberation styles
5. **Confidence calibration** — Every answer comes with a calibrated confidence score

## License

MIT
