"""Model router: sends prompts to LLMs via OpenRouter or local providers."""
import os
import httpx
from ..config import CouncilConfig, ModelConfig


class ModelRouter:
    def __init__(self, config: CouncilConfig):
        self.config = config
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = config.openrouter_base_url

    async def query(self, model: ModelConfig, messages: list[dict], temperature: float = 0.7) -> str:
        """Send a query to a model and return the response text."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model.id,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def query_all(self, messages: list[dict], temperature: float = 0.7) -> dict[str, str]:
        """Query all council models in parallel."""
        import asyncio
        tasks = {m.id: self.query(m, messages, temperature) for m in self.config.models}
        results = {}
        for model_id, task in tasks.items():
            try:
                results[model_id] = await task
            except Exception as e:
                results[model_id] = f"[ERROR: {e}]"
        return results
