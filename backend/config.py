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
        ModelConfig(
            id="anthropic/claude-opus-4", name="Opus",
            role="architect",
            provider="openrouter",
            strengths=["architecture", "complex-reasoning", "paper-writing", "security-audit"],
        ),
        ModelConfig(
            id="openai/codex-mini", name="Codex",
            role="coordinator",
            provider="openrouter",
            strengths=["parallel-execution", "server-commands", "fast-iteration", "bulk-work"],
        ),
        ModelConfig(
            id="anthropic/claude-sonnet-4-6", name="OpenCode",
            role="implementer",
            provider="openrouter",
            strengths=["implementation", "testing", "doc-updates", "code-review"],
        ),
        ModelConfig(
            id="anthropic/claude-sonnet-4-5", name="Sonnet",
            role="reviewer",
            provider="openrouter",
            strengths=["code-review", "table-eligibility", "verification", "quality-gate"],
        ),
        ModelConfig(
            id="anthropic/claude-haiku-3.5", name="Haiku",
            role="speedster",
            provider="openrouter",
            strengths=["lint", "format-check", "pre-screening", "fast-triage"],
        ),
        ModelConfig(
            id="deepseek/deepseek-chat", name="DeepSeek",
            role="bulk-worker",
            provider="openrouter",
            strengths=["translation", "bulk-text", "chinese-content", "long-generation"],
        ),
    ])
    chairman: str = "anthropic/claude-opus-4"
    default_protocol: str = "council"
    confidence_threshold: float = 0.7
    consensus_rounds_max: int = 5
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
