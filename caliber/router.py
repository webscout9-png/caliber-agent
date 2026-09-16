from __future__ import annotations

from typing import Dict

from .config import load_config
from .models import BEST_DEFAULTS

TASK_KEYWORDS: Dict[str, list[str]] = {
    "coding": [
        "code", "implement", "function", "class", "bug", "fix", "refactor",
        "script", "program", "python", "javascript", "typescript", "api",
        "debug", "test", "unit test", "algorithm", "optimize",
    ],
    "reasoning": [
        "reason", "think", "analyze", "why", "logic", "prove", "deduce",
        "infer", "compare", "evaluate", "trade-off", "pros and cons",
    ],
    "planning": [
        "plan", "strategy", "steps", "roadmap", "architecture", "design",
        "outline", "break down", "approach", "structure",
    ],
    "search": [
        "search", "find", "lookup", "current", "latest", "news", "web",
        "up to date", "recent",
    ],
    "writing": [
        "write", "draft", "email", "blog", "article", "documentation",
        "rewrite", "summarize", "explain", "describe", "report",
    ],
}


def classify_task(text: str) -> str:
    lower = text.lower()
    scores: Dict[str, int] = {k: 0 for k in TASK_KEYWORDS}
    for task, kws in TASK_KEYWORDS.items():
        for kw in kws:
            if kw in lower:
                scores[task] += 1 + (1 if len(kw) > 6 else 0)
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "default"
    return best


def get_model_for_task(task: str) -> str:
    cfg = load_config()
    if cfg.get("model_mode") == "custom":
        custom = cfg.get("custom_models", {})
        return (
            custom.get(task)
            or custom.get("default")
            or BEST_DEFAULTS.get("default", "openai/gpt-4o-mini")
        )
    best = cfg.get("best_models", {})
    return (
        best.get(task)
        or BEST_DEFAULTS.get(task)
        or BEST_DEFAULTS.get("default", "openai/gpt-4o-mini")
    )
