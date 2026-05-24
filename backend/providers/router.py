"""Model router: sends prompts to real multi-model council via multiple providers."""
import asyncio
import os
import httpx
from ..config import CouncilConfig, ModelConfig

# ── Endpoint + key constants ──────────────────────────────────────────────────
_KEY_ROTATOR = "http://127.0.0.1:8990/v1"
_KEY_ROTATOR_KEY = "xiangsumao"
_SBBBBB = "http://api.sbbbbbbbbb.xyz/v1"
_SBBBBB_KEY = "sk-nT6k0QhaV2c69bEWjjZWiIRKFDOt7d0eSgs5BefIPutgZS0V"
_DEEPSEEK = "https://api.deepseek.com/v1"
_DEEPSEEK_KEY = "sk-977ee717bb8449368e1f6ed35cde3fc5"

# ── Real model routing table ──────────────────────────────────────────────────
# Maps council role → (model_id, base_url, api_key, format)
# format: "anthropic" | "openai"
_ROLE_ROUTING: dict[str, tuple[str, str, str, str]] = {
    "architect":   ("claude-opus-4-7",   _SBBBBB,      _SBBBBB_KEY,      "anthropic"),
    "coordinator": ("gpt-5.5",           _SBBBBB,      _SBBBBB_KEY,      "openai"),
    "implementer": ("claude-opus-4-7",   _SBBBBB,      _SBBBBB_KEY,      "anthropic"),
    "reviewer":    ("gpt-5.5",           _SBBBBB,      _SBBBBB_KEY,      "openai"),
    "speedster":   ("claude-opus-4-7",   _SBBBBB,      _SBBBBB_KEY,      "anthropic"),
    "bulk-worker": ("deepseek-chat",     _DEEPSEEK,    _DEEPSEEK_KEY,    "openai"),
    "generalist":  ("claude-opus-4-7",   _SBBBBB,      _SBBBBB_KEY,      "anthropic"),
}

# ── Role system prompts ───────────────────────────────────────────────────────
_ROLE_SYSTEM_PROMPTS: dict[str, str] = {
    "architect": (
        "You are Opus, the architect. Your role: deep reasoning, global perspective, "
        "architectural decisions, security audits, and long-horizon thinking. "
        "Be thorough, consider second-order effects, and flag risks others might miss."
    ),
    "coordinator": (
        "You are Codex, the coordinator. Your role: task decomposition, parallel execution, "
        "fast iteration, and bulk work. Break problems into concrete steps. "
        "Be direct, action-oriented, and focus on what can be done immediately."
    ),
    "implementer": (
        "You are OpenCode, the implementer. Your role: concrete implementation, testing, "
        "code review, and doc updates. Focus on working solutions, edge cases, and "
        "practical feasibility. Show your work."
    ),
    "reviewer": (
        "You are Sonnet, the reviewer. Your role: code review, verification, quality gates, "
        "and second opinions. Be precise, find what others missed, and give actionable feedback. "
        "Warm but direct."
    ),
    "speedster": (
        "You are Haiku, the speedster. Your role: fast triage, pre-screening, lint checks, "
        "and yes/no decisions. Be extremely concise. One sentence answers when possible."
    ),
    "bulk-worker": (
        "你是椴搁奔（DeepSeek），负责批量文本处理、翻译、摘要和分类。"
        "专注于中文内容生成和大量文本的高效处理。直接给出结果，不废话。"
    ),
    "generalist": (
        "You are a council member. Provide a thoughtful, balanced perspective. "
        "Be specific and evidence-based."
    ),
}


class ModelRouter:
    def __init__(self, config: CouncilConfig):
        self.config = config

    def _get_routing(self, model: ModelConfig) -> tuple[str, str, str, str]:
        """Get (model_id, base_url, api_key, format) for a council member."""
        return _ROLE_ROUTING.get(model.role, _ROLE_ROUTING["generalist"])

    def _get_system_prompt(self, model: ModelConfig, context: str = "") -> str:
        base = _ROLE_SYSTEM_PROMPTS.get(model.role, _ROLE_SYSTEM_PROMPTS["generalist"])
        if context:
            return f"{base}\n\nProject context:\n{context}"
        return base

    async def query(
        self,
        model: ModelConfig,
        messages: list[dict],
        temperature: float = 0.7,
        context: str = "",
    ) -> str:
        """Send a query to the real model for this role."""
        model_id, base_url, api_key, fmt = self._get_routing(model)
        system = self._get_system_prompt(model, context)

        for attempt in range(3):
            try:
                if fmt == "anthropic":
                    return await self._call_anthropic(
                        model_id, base_url, api_key, messages, system, temperature
                    )
                else:
                    return await self._call_openai(
                        model_id, base_url, api_key, messages, system, temperature
                    )
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == 2:
                    return f"[{model.name} ERROR: {e}]"
                await asyncio.sleep(2 ** attempt)
        return f"[{model.name} ERROR: max retries]"

    async def _call_anthropic(
        self,
        model_id: str,
        base_url: str,
        api_key: str,
        messages: list[dict],
        system: str,
        temperature: float,
    ) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload: dict = {
                "model": model_id,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": temperature,
            }
            if system:
                payload["system"] = system
            r = await client.post(
                f"{base_url.rstrip('/')}/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"]

    async def _call_openai(
        self,
        model_id: str,
        base_url: str,
        api_key: str,
        messages: list[dict],
        system: str,
        temperature: float,
    ) -> str:
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": all_messages,
                    "temperature": temperature,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    async def query_all(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        context: str = "",
    ) -> dict[str, str]:
        """Query all council models in parallel."""
        async def safe_query(model: ModelConfig) -> tuple[str, str]:
            result = await self.query(model, messages, temperature, context)
            return model.name, result

        pairs = await asyncio.gather(*[safe_query(m) for m in self.config.models])
        return dict(pairs)
