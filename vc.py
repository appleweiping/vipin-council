#!/usr/bin/env python3
"""
vc — Vipin Council CLI
Multi-LLM deliberation from your terminal.

Usage:
  vc                              # interactive REPL
  vc "your question"              # one-shot query (council protocol)
  vc "your question" -p debate    # specify protocol
  vc sessions                     # list recent sessions
  vc show <id>                    # replay a session
  vc models                       # list configured models
  vc protocols                    # list protocols
  vc status                       # check backend health
"""
import sys
import os
# Ensure project root is on sys.path so `from backend.*` works whether
# invoked as `python vc.py`, `python -m vc`, or via the `vc` entry-point.
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)
import argparse
import asyncio
import json
import os
import sys
import textwrap
import uuid
import time
import threading
import itertools
import shutil
from datetime import datetime
from pathlib import Path

# ── ANSI colour palette ───────────────────────────────────────────────────────
R = "\033[0m"
BOLD = "\033[1m"; DIM = "\033[2m"; ITALIC = "\033[3m"
BLACK = "\033[30m"; RED = "\033[31m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
BLUE = "\033[34m"; MAGENTA = "\033[35m"; CYAN = "\033[36m"; WHITE = "\033[37m"
BBLACK = "\033[90m"; BRED = "\033[91m"; BGREEN = "\033[92m"; BYELLOW = "\033[93m"
BBLUE = "\033[94m"; BMAGENTA = "\033[95m"; BCYAN = "\033[96m"; BWHITE = "\033[97m"

def c(*args):
    """c(text, *codes) or c(*codes, text) — wrap text in ANSI codes."""
    codes = [a for a in args if isinstance(a, str) and a.startswith("\033")]
    texts = [a for a in args if not (isinstance(a, str) and a.startswith("\033"))]
    return "".join(codes) + str(texts[0] if texts else "") + R

def hr(char="─", width=None):
    w = width or min(shutil.get_terminal_size().columns, 88)
    return c(char * w, DIM)

def wrap(text: str, width: int = None, indent: str = "  ") -> str:
    w = width or min(shutil.get_terminal_size().columns - 4, 84)
    lines = []
    for para in str(text).split("\n"):
        if para.strip() == "":
            lines.append("")
        else:
            lines.extend(textwrap.wrap(para, w, initial_indent=indent, subsequent_indent=indent))
    return "\n".join(lines)

# ── Protocol metadata ─────────────────────────────────────────────────────────
PROTOCOLS = {
    "council":    ("⚖", BBLUE,    "All models → peer review → chairman synthesis"),
    "debate":     ("⚔", BRED,     "Pro vs con → rebuttals → judge verdict"),
    "redteam":    ("🔴", BYELLOW,  "Defend → attack → improve iteratively"),
    "consensus":  ("🤝", BGREEN,   "Iterative rounds until agreement threshold met"),
    "specialist": ("🎯", BMAGENTA, "Classify domain → route to expert → verify"),
    "tournament": ("🏆", BYELLOW,  "Bracket elimination, best answer wins"),
}

# ── Spinner ───────────────────────────────────────────────────────────────────
class Spinner:
    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, msg: str = "Thinking", color: str = CYAN):
        self.msg = msg
        self.color = color
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._start_time = 0.0

    def _run(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop.is_set():
                break
            elapsed = time.time() - self._start_time
            line = f"\r  {c(frame, self.color)} {self.msg}  {c(f'{elapsed:.1f}s', DIM)}  "
            sys.stdout.write(line)
            sys.stdout.flush()
            time.sleep(0.08)
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._start_time = time.time()
        self._t.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._t.join()

# ── Formatting helpers ────────────────────────────────────────────────────────
def print_header():
    cols = shutil.get_terminal_size().columns
    print()
    print(c("  ⚡ Vipin Council", BOLD, BMAGENTA) + "  " + c("v2.1", DIM))
    print(c("  Multi-LLM Deliberation System", DIM))
    print(hr())
    _show_startup_context()


def _show_startup_context():
    """Show mailbox messages and active projects on startup."""
    try:
        from backend.memory.shared_memory import load_shared_memory, read_mailbox, mark_messages_read
        msgs = read_mailbox("vc")
        if msgs:
            print(f"  {c('📬 Mailbox', BOLD, BYELLOW)}  {c(f'{len(msgs)} unread', DIM)}")
            for m in msgs[:3]:
                print(f"  {c('·', DIM)} {c(m.get('from', '?'), BCYAN)}: {m.get('subject', '')[:60]}")
            mark_messages_read("vc")
            print()
        ctx = load_shared_memory()
        if ctx.projects:
            print(f"  {c('Active Projects', BOLD, BCYAN)}")
            for p in ctx.projects[:4]:
                prio = p["priority"]
                name = p["name"]
                status = p["status"][:50]
                print(f"  {c(f'P{prio}', DIM)} {c(name, BOLD)}  {c(status, DIM)}")
            print()
    except Exception:
        pass

def print_query_echo(query: str, protocol: str):
    icon, color, _ = PROTOCOLS.get(protocol, ("?", WHITE, ""))
    print()
    print(f"  {c('Query', BOLD, DIM)}  {c(query, ITALIC, WHITE)}")
    print(f"  {c('Protocol', BOLD, DIM)}  {c(icon + ' ' + protocol.capitalize(), color, BOLD)}")
    print(hr())

def print_confidence(value: float):
    pct = int((value or 0) * 100)
    if pct >= 70:   color, label = BGREEN,  "high"
    elif pct >= 40: color, label = BYELLOW, "moderate"
    else:           color, label = BRED,    "low"
    bar_len = 24
    filled = int(bar_len * pct / 100)
    bar = c("█" * filled, color) + c("░" * (bar_len - filled), BBLACK)
    print(f"  {c('Confidence', BOLD, DIM)}  {bar}  {c(f'{pct}%', color, BOLD)}  {c(label, DIM)}")

def print_final_answer(text: str):
    print()
    print(f"  {c('✦ Final Answer', BOLD, BGREEN)}")
    print(hr("─"))
    print(wrap(text))
    print(hr("─"))

def print_dissent(dissent: list):
    if not dissent:
        return
    print()
    print(f"  {c('⚠ Dissenting Views', BOLD, BYELLOW)}  {c(f'({len(dissent)})', DIM)}")
    for d in dissent:
        snippet = d[:300] + ("…" if len(d) > 300 else "")
        print(wrap(snippet, indent="    "))

def print_audit(trail: list, verbose: bool):
    if not trail or not verbose:
        return
    print()
    print(f"  {c('Audit Trail', BOLD, DIM)}")
    for step in trail:
        print(f"    {c('·', DIM)} {c(json.dumps(step), BBLACK)}")

def print_stages(stages: list, verbose: bool):
    if not stages or not verbose:
        return
    print()
    print(f"  {c('Deliberation Stages', BOLD, DIM)}")
    for i, stage in enumerate(stages):
        name = stage.get("name", f"Stage {i+1}")
        print(f"\n  {c(f'  {i+1}. {name}', BOLD, BBLUE)}")
        print(hr("·"))
        responses = stage.get("responses", {})
        for model_id, resp in responses.items():
            short = model_id.split("/")[-1]
            print(f"\n    {c(short, BOLD, CYAN)}")
            print(wrap(resp[:600] + ("…" if len(resp) > 600 else ""), indent="      "))
        if "agreement_ratio" in stage:
            pct = int(stage["agreement_ratio"] * 100)
            print(f"\n    {c('Agreement:', DIM)} {c(f'{pct}%', BGREEN)}")

def print_result(result: dict, verbose: bool = False):
    print_confidence(result.get("confidence", 0))
    print_final_answer(result.get("final_answer", ""))
    print_dissent(result.get("dissent", []))
    print_stages(result.get("stages", []), verbose)
    print_audit(result.get("audit_trail", []), verbose)
    sid = result.get("id", result.get("session_id", ""))
    if sid:
        print(f"\n  {c('Session ID:', DIM)} {c(sid[:8], BBLACK)}  {c('(vc show ' + sid[:8] + ')', DIM)}")
    print()

# ── Data directory ────────────────────────────────────────────────────────────
def data_dir() -> Path:
    d = Path(__file__).parent / "data" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_result(result: dict):
    sid = result.get("id") or result.get("session_id")
    if not sid:
        return
    (data_dir() / f"{sid}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )

# ── Core query ────────────────────────────────────────────────────────────────
async def run_query(query: str, protocol: str, verbose: bool) -> dict | None:
    try:
        from backend.config import CouncilConfig
        from backend.council.orchestrator import Orchestrator
        from backend.council.session import Session
    except ImportError as e:
        print(c(f"\n  ✗ Import error: {e}", BRED))
        print(c("  Run: pip install -e .", DIM))
        return None

    config = CouncilConfig()
    orchestrator = Orchestrator(config)
    session = Session(
        id=str(uuid.uuid4()),
        query=query,
        protocol=protocol,
        context=None,
        created_at=datetime.utcnow().isoformat(),
    )

    print_query_echo(query, protocol)

    icon, color, _ = PROTOCOLS.get(protocol, ("?", WHITE, ""))
    with Spinner(f"Running {icon} {protocol} protocol", color):
        result = await orchestrator.run(session)

    result_dict = result.to_dict()
    save_result(result_dict)
    return result_dict

# ── Sub-commands ──────────────────────────────────────────────────────────────
def cmd_sessions():
    files = sorted(data_dir().glob("*.json"), reverse=True)[:25]
    if not files:
        print(c("\n  No sessions yet.\n", DIM))
        return
    print(f"\n  {c('Recent Sessions', BOLD)}")
    print(hr())
    for f in files:
        try:
            d = json.loads(f.read_text())
            ts = d.get("created_at", "")[:16].replace("T", " ")
            proto = d.get("protocol", "?")
            icon, color, _ = PROTOCOLS.get(proto, ("?", WHITE, ""))
            q = d.get("query", "")[:55]
            sid = c(d.get("id", "")[:8], BBLACK)
            proto_str = c(f"{icon} {proto}", color)
            print(f"  {sid}  {c(ts, DIM)}  {proto_str:<28}  {q}")
        except Exception:
            pass
    print(hr())
    print()

def cmd_show(session_id: str, verbose: bool):
    matches = list(data_dir().glob(f"{session_id}*.json"))
    if not matches:
        print(c(f"\n  ✗ Session not found: {session_id}\n", BRED))
        sys.exit(1)
    result = json.loads(matches[0].read_text())
    print_query_echo(result.get("query", ""), result.get("protocol", "council"))
    print_result(result, verbose)

def cmd_models():
    try:
        from backend.config import CouncilConfig
        config = CouncilConfig()
    except ImportError:
        print(c("\n  Run: pip install -e .\n", BRED)); sys.exit(1)

    role_colors = {
        "architect": BMAGENTA, "coordinator": BBLUE, "implementer": BGREEN,
        "reviewer": BYELLOW, "speedster": BCYAN, "bulk-worker": DIM,
    }
    print(f"\n  {c('Council Models', BOLD)}")
    print(hr())
    for m in config.models:
        rc = role_colors.get(m.role, WHITE)
        strengths = c(", ".join(m.strengths[:3]), BBLACK)
        print(f"  {c(m.name, BOLD):<22} {c(m.role, rc):<20} {c(m.id, DIM)}")
        print(f"  {'':22} {strengths}")
        print()
    print(f"  {c('Chairman:', BOLD, DIM)} {c(config.chairman, BMAGENTA)}")
    print(hr())
    print()

def cmd_protocols():
    print(f"\n  {c('Deliberation Protocols', BOLD)}")
    print(hr())
    for pid, (icon, color, desc) in PROTOCOLS.items():
        print(f"  {c(icon + ' ' + pid, BOLD, color):<30} {c(desc, DIM)}")
    print(hr())
    print()

def cmd_status():
    import httpx
    print(f"\n  {c('Backend Status', BOLD)}")
    print(hr())
    try:
        r = httpx.get("http://localhost:8000/api/health", timeout=3)
        data = r.json()
        print(f"  {c('●', BGREEN)} Backend  {c('http://localhost:8000', BCYAN)}")
        print(f"  {c('●', BGREEN)} Models   {c(str(data.get('models', '?')), BWHITE)} configured")
        print(f"  {c('●', BGREEN)} Version  {c(data.get('version', '?'), DIM)}")
    except Exception as e:
        print(f"  {c('●', BRED)} Backend unreachable  {c(str(e), DIM)}")
        print(f"  {c('→', DIM)} Run: uvicorn backend.main:app --reload --port 8000")
    print(hr())
    print()


def cmd_projects():
    """Show active research projects from shared memory."""
    try:
        from backend.memory.shared_memory import load_shared_memory
        ctx = load_shared_memory()
        if not ctx.projects:
            print(c("\n  No active projects found in shared memory.\n", DIM))
            return
        print(f"\n  {c('Active Research Projects', BOLD, BCYAN)}")
        print(hr())
        for p in ctx.projects:
            prio = p["priority"]
            name = p["name"]
            direction = p["direction"][:70]
            status = p["status"][:70]
            print(f"  {c(f'P{prio}', BYELLOW)} {c(name, BOLD)}")
            print(f"     {c('Direction:', DIM)} {direction}")
            print(f"     {c('Status:', DIM)} {c(status, DIM)}")
        print(hr())
        print()
    except Exception as e:
        print(c(f"\n  ✗ Could not load projects: {e}\n", BRED))


def cmd_context():
    """Show the project context that will be injected into queries."""
    try:
        from backend.memory.shared_memory import load_shared_memory
        ctx = load_shared_memory()
        block = ctx.as_context_block()
        if not block:
            print(c("\n  No context available.\n", DIM))
            return
        print(f"\n  {c('Injected Context', BOLD, BCYAN)}")
        print(hr())
        for line in block.split("\n"):
            print(f"  {line}")
        print(hr())
        print()
    except Exception as e:
        print(c(f"\n  ✗ Could not load context: {e}\n", BRED))

# ── Interactive REPL ──────────────────────────────────────────────────────────
REPL_HELP = f"""
  {c('Commands', BOLD)}
  {c('/protocol <name>', CYAN)}   switch protocol  (council, debate, redteam, consensus, specialist, tournament)
  {c('/verbose', CYAN)}           toggle verbose mode (show all stages)
  {c('/sessions', CYAN)}          list recent sessions
  {c('/models', CYAN)}            list configured models
  {c('/protocols', CYAN)}         list all protocols
  {c('/status', CYAN)}            check backend health
  {c('/projects', CYAN)}          show active research projects
  {c('/context', CYAN)}           show current project context injected into queries
  {c('/clear', CYAN)}             clear screen
  {c('/help', CYAN)}              show this help
  {c('/quit', CYAN)}  or Ctrl-C   exit

  {c('Tip:', DIM)} Enter to send · Shift+Enter for newline
"""

async def repl():
    print_header()
    protocol = "council"
    verbose = False

    print(f"  {c('Type your question and press Enter.', DIM)}  {c('/help for commands', BBLACK)}")
    print()

    while True:
        icon, color, _ = PROTOCOLS.get(protocol, ("?", WHITE, ""))
        prompt = f"  {c(icon, color)} {c(protocol, BOLD, color)} {c('›', DIM)} "

        try:
            query = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {c('Goodbye.', DIM)}\n")
            break

        if not query:
            continue

        # Slash commands
        if query.startswith("/"):
            parts = query.split()
            cmd = parts[0].lower()

            if cmd in ("/quit", "/exit", "/q"):
                print(f"\n  {c('Goodbye.', DIM)}\n")
                break
            elif cmd == "/help":
                print(REPL_HELP)
            elif cmd == "/clear":
                os.system("cls" if os.name == "nt" else "clear")
                print_header()
            elif cmd == "/verbose":
                verbose = not verbose
                print(f"  {c('Verbose mode:', DIM)} {c('on', BGREEN) if verbose else c('off', BBLACK)}\n")
            elif cmd == "/sessions":
                cmd_sessions()
            elif cmd == "/models":
                cmd_models()
            elif cmd == "/status":
                cmd_status()
            elif cmd == "/protocol" and len(parts) > 1:
                p = parts[1].lower()
                if p in PROTOCOLS:
                    protocol = p
                    icon2, color2, desc = PROTOCOLS[p]
                    print(f"  {c('Protocol →', DIM)} {c(icon2 + ' ' + p, BOLD, color2)}  {c(desc, DIM)}\n")
                else:
                    print(c(f"  Unknown protocol: {p}. Options: {', '.join(PROTOCOLS)}\n", BRED))
            elif cmd == "/projects":
                cmd_projects()
            elif cmd == "/context":
                cmd_context()
            else:
                print(c(f"  Unknown command: {cmd}. Type /help\n", BRED))
            continue

        # Regular query
        result = await run_query(query, protocol, verbose)
        if result:
            print_result(result, verbose)

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="vc",
        description="Vipin Council — multi-LLM deliberation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          vc                                    # interactive REPL
          vc "What is the best way to learn Rust?"
          vc "Should I use microservices?" -p debate
          vc "My startup idea: X" -p redteam
          vc "Explain transformers" -p tournament -v
          vc sessions
          vc show abc123
          vc models
          vc protocols
          vc status
        """),
    )
    parser.add_argument("query_or_cmd", nargs="?",
                        help="Query text, or: sessions / show / models / protocols / status")
    parser.add_argument("session_id",   nargs="?", help="Session ID (for 'show')")
    parser.add_argument("-p", "--protocol", default="council",
                        choices=list(PROTOCOLS.keys()),
                        help="Deliberation protocol (default: council)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show all stages and audit trail")

    args = parser.parse_args()

    # No args → interactive REPL
    if not args.query_or_cmd:
        asyncio.run(repl())
        return

    cmd = args.query_or_cmd.lower()

    if cmd == "sessions":
        cmd_sessions()
    elif cmd == "show":
        if not args.session_id:
            print(c("Usage: vc show <session_id>", BRED)); sys.exit(1)
        cmd_show(args.session_id, args.verbose)
    elif cmd == "models":
        cmd_models()
    elif cmd == "protocols":
        cmd_protocols()
    elif cmd == "status":
        cmd_status()
    else:
        # One-shot query
        print_header()
        result = asyncio.run(run_query(args.query_or_cmd, args.protocol, args.verbose))
        if result:
            print_result(result, args.verbose)


if __name__ == "__main__":
    main()
