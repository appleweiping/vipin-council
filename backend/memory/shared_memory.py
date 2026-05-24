"""Shared memory loader for Vipin Council — reads active project context."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_MEMORY_ROOT = Path(r"D:\research\Vipin's Knowledgebase\memory")
_MAILBOX_ROOT = Path(r"D:\devtools\agent-hub\state")


@dataclass
class SharedMemoryContext:
    projects: list[dict] = field(default_factory=list)   # {name, direction, status, priority}
    rules: list[str] = field(default_factory=list)
    raw_summary: str = ""

    def as_context_block(self) -> str:
        if not self.projects:
            return ""
        lines = ["=== Active Research Projects ==="]
        for p in self.projects:
            lines.append(f"[P{p['priority']}] {p['name']}: {p['direction']} | {p['status'][:60]}")
        if self.rules:
            lines.append("\n=== Key Rules ===")
            lines.extend(f"- {r}" for r in self.rules[:5])
        return "\n".join(lines)

    def find_project(self, query: str) -> dict | None:
        q = query.lower()
        for p in self.projects:
            if p["name"].lower() in q or any(w in q for w in p["name"].lower().split("/")):
                return p
        return None


def load_shared_memory() -> SharedMemoryContext:
    ctx = SharedMemoryContext()
    _load_projects(ctx)
    _load_rules(ctx)
    return ctx


def _load_projects(ctx: SharedMemoryContext) -> None:
    status_file = _MEMORY_ROOT / "facts" / "all-projects-status.md"
    if not status_file.exists():
        return
    try:
        text = status_file.read_text(encoding="utf-8", errors="replace")
        ctx.raw_summary = text[:2000]
        for m in re.finditer(
            r'\|\s*(\d+)\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|',
            text
        ):
            ctx.projects.append({
                "priority": int(m.group(1)),
                "name": m.group(2).strip(),
                "direction": m.group(3).strip(),
                "status": m.group(4).strip()[:80],
            })
    except Exception:
        pass


def _load_rules(ctx: SharedMemoryContext) -> None:
    rules_file = _MEMORY_ROOT / "decisions" / "research-hard-rules.md"
    if not rules_file.exists():
        return
    try:
        text = rules_file.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'^[-*]\s+(.+)$', text, re.MULTILINE):
            rule = m.group(1).strip()
            if len(rule) > 20:
                ctx.rules.append(rule)
                if len(ctx.rules) >= 8:
                    break
    except Exception:
        pass


def read_mailbox(agent: str = "vc") -> list[dict]:
    mailbox_file = _MAILBOX_ROOT / f"messages-{agent}.json"
    if not mailbox_file.exists():
        return []
    try:
        data = json.loads(mailbox_file.read_text(encoding="utf-8"))
        return [m for m in data.get("messages", []) if not m.get("read", False)]
    except Exception:
        return []


def mark_messages_read(agent: str = "vc") -> None:
    mailbox_file = _MAILBOX_ROOT / f"messages-{agent}.json"
    if not mailbox_file.exists():
        return
    try:
        data = json.loads(mailbox_file.read_text(encoding="utf-8"))
        for m in data.get("messages", []):
            m["read"] = True
        mailbox_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
