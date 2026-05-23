# CLAUDE.md - Vipin Council

Multi-LLM deliberation system with 6 protocols.

## Quick Start
```bash
cd D:\research\vipin-council
pip install -e .
cp .env.example .env   # add OPENROUTER_API_KEY

# Option A: start.cmd (Windows, opens two terminal windows)
start.cmd

# Option B: manual
uvicorn backend.main:app --reload --port 8000   # backend
cd frontend && npm run dev                       # frontend (http://localhost:5173)
python vc.py                                     # CLI interactive REPL
```

## Architecture
- backend/council/ — orchestrator and session management
- backend/protocols/ — 6 deliberation protocols
- backend/providers/ — LLM API routing (OpenRouter)
- backend/memory/ — cross-session performance tracking
- backend/engine/ — smart router, self-refine, tree-of-thoughts, task decomposer
- frontend/ — React + Vite UI
- vc.py — CLI tool (interactive REPL + one-shot)

## Protocols
1. Council: all answer → peer review → chairman synthesis
2. Debate: pro vs con → rebuttals → judge verdict
3. RedTeam: defend → attack → improve
4. Consensus: iterative rounds until convergence
5. Specialist: classify domain → route to expert → verify
6. Tournament: bracket elimination

## CLI Commands (REPL mode)
/protocol <name>   switch protocol
/verbose           toggle verbose (show all stages)
/sessions          list recent sessions
/models            list configured models
/status            check backend health
/clear             clear screen
/help              show help
/quit              exit

## Known Issues Fixed (2026-05-24)
- router.py query_all() was sequential, now uses asyncio.gather
- task_decomposer.py ready tasks were sequential, now parallel
- config.py OpenCode and Sonnet had same model ID (now 4.6 vs 4.5)
- consensus_protocol.py agreement_ratio variable scope fixed

