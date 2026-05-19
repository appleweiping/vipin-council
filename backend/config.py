"""Council configuration."""
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    id: str
    name: str
    role: str = "generalist"  # generalist, architect, critic, researcher, practitioner
    provider: str = "openrouter"
    strengths: list[str] = field(default_factory=list)
    cost_per_1k: float = 0.0


@dataclass
class CouncilConfig:
    models: list[ModelConfig] = field(default_factory=lambda: [
        ModelConfig(id="anthropic/claude-sonnet-4", name="Claude Sonnet", role="architect", strengths=["reasoning", "code", "analysis"]),
        ModelConfig(id="openai/gpt-4o", name="GPT-4o", role="generalist", strengths=["breadth", "instruction-following"]),
        ModelConfig(id="google/gemini-2.5-pro", name="Gemini Pro", role="researcher", strengths=["research", "multimodal", "long-context"]),
        ModelConfig(id="x-ai/grok-3", name="Grok 3", role="critic", strengths=["directness", "unconventional"]),
        ModelConfig(id="deepseek/deepseek-r1", name="DeepSeek R1", role="practitioner", strengths=["math", "code", "reasoning"]),
    ])
    chairman: str = "anthropic/claude-sonnet-4"
    default_protocol: str = "council"
    confidence_threshold: float = 0.7
    consensus_rounds_max: int = 5
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
