"""Performance tracker: remembers which models perform well on which topics."""
import json
from pathlib import Path
from collections import defaultdict

MEMORY_PATH = Path(__file__).parent.parent.parent / "data" / "model_performance.json"


class PerformanceTracker:
    def __init__(self):
        self.scores: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._load()

    def record(self, model_id: str, domain: str, score: float):
        self.scores[model_id][domain] = (self.scores[model_id][domain] + score) / 2
        self._save()

    def get_best_for(self, domain: str) -> str | None:
        best_id, best_score = None, 0.0
        for model_id, domains in self.scores.items():
            if domains.get(domain, 0) > best_score:
                best_id = model_id
                best_score = domains[domain]
        return best_id

    def _load(self):
        if MEMORY_PATH.exists():
            data = json.loads(MEMORY_PATH.read_text())
            for mid, domains in data.items():
                for domain, score in domains.items():
                    self.scores[mid][domain] = score

    def _save(self):
        MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_PATH.write_text(json.dumps(dict(self.scores), indent=2))
