# CLAUDE.md - Vipin Council

Multi-LLM deliberation system with 6 protocols.

## Quick Start
```bash
cd D:\research\vipin-council
pip install -e .
uvicorn backend.main:app --reload
```

## Architecture
- backend/council/ — orchestrator and session management
- backend/protocols/ — 6 deliberation protocols
- backend/providers/ — LLM API routing (OpenRouter)
- backend/memory/ — cross-session performance tracking
- frontend/ — React UI

## Protocols
1. Council: all answer → peer review → chairman synthesis
2. Debate: pro vs con → rebuttals → judge verdict
3. RedTeam: defend → attack → improve
4. Consensus: iterative rounds until convergence
5. Specialist: classify domain → route to expert → verify
6. Tournament: bracket elimination
