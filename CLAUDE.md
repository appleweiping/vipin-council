# CLAUDE.md - Vipin Council

## Session Start (mandatory)

On every session start, run these in order:
1. `memory_smart_search` with the current task description (agentmemory MCP)
2. Read `D:\research\Vipin's Knowledgebase\memory\INDEX.md` for shared context
3. Check mailbox: `D:\devtools\agent-hub\state\messages-vc.json` for unread messages

After significant work, call `memory_save` with key decisions and findings.

## Agent Identity

- **Name**: vc (Vipin Council)
- **Role**: Multi-LLM deliberation — 6 protocols (council, debate, red-team, consensus, specialist, tournament)
- **Mailbox**: `D:\devtools\agent-hub\state\messages-vc.json`
- **Shared memory**: `D:\research\Vipin's Knowledgebase\memory\`
- **agentmemory URL**: `http://localhost:3111` (env: `AGENTMEMORY_URL`)

## Multi-Agent Rules

- Follow `D:\research\Vipin's Knowledgebase\AGENTS.md` for collaboration rules
- Write durable findings to `D:\research\Vipin's Knowledgebase\memory\` after sessions
- Do not store secrets or API keys in memory
- For non-trivial tasks: read `D:\agent-resources\SKILL-INDEX.md` first and use the matching skill

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

