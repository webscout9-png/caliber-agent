from __future__ import annotations

from typing import Any, Dict, List

from .config import load_config
from .models import list_models_for_task

TASK_KEYWORDS = {
    "coding": ["code", "implement", "function", "class", "bug", "fix", "refactor", "script", "program", "python", "javascript", "typescript", "api"],
    "reasoning": ["reason", "think", "analyze", "why", "logic", "prove", "deduce", "infer"],
    "planning": ["plan", "strategy", "steps", "roadmap", "architecture", "design", "outline"],
    "search": ["search", "find", "lookup", "current", "latest", "news", "web"],
    "writing": ["write", "draft", "email", "blog", "article", "story", "documentation"],
}

def classify_task(text: str) -> str:
    lower = text.lower()
    scores = {k: 0 for k in TASK_KEYWORDS}
    for task, kws in TASK_KEYWORDS.items():
        for kw in kws:
            if kw in lower:
                scores[task] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "default"
    return best

def get_model_for_task(task: str) -> str:
    cfg = load_config()
    if cfg.get("model_mode") == "custom":
        return cfg.get("custom_models", {}).get(task) or cfg.get("custom_models", {}).get("default") or "openai/gpt-4o-mini"
    # best mode
    return cfg.get("best_models", {}).get(task) or cfg.get("best_models", {}).get("default") or "openai/gpt-4o"

def decompose(user_request: str, effort: str) -> List[Dict[str, str]]:
    """Simple deterministic decomposition for v0.1. Later versions can use a planner model."""
    task = classify_task(user_request)
    steps = []

    if effort in ("low",):
        steps.append({"type": task, "instruction": user_request})
    elif effort in ("medium", "high"):
        if task == "coding":
            steps = [
                {"type": "planning", "instruction": f"Create a clear plan and architecture for: {user_request}"},
                {"type": "coding", "instruction": f"Implement the solution based on the plan. Request: {user_request}"},
                {"type": "reasoning", "instruction": "Review the code for bugs, edge cases and improvements."},
            ]
        elif task == "planning":
            steps = [
                {"type": "planning", "instruction": user_request},
                {"type": "reasoning", "instruction": "Critique and improve the plan."},
            ]
        else:
            steps = [
                {"type": task, "instruction": user_request},
                {"type": "reasoning", "instruction": f"Review and refine the previous output for quality."},
            ]
    else:  # max / ultra
        steps = [
            {"type": "planning", "instruction": f"Break down this request into precise sub-tasks and produce a detailed plan: {user_request}"},
            {"type": "reasoning", "instruction": "Analyze risks, edge cases and success criteria."},
            {"type": task if task != "default" else "default", "instruction": f"Execute the core work: {user_request}"},
            {"type": "writing", "instruction": "Polish the final answer into a clear, complete response."},
        ]
        if effort == "ultra":
            steps.insert(2, {"type": "search", "instruction": f"Gather any missing up-to-date information needed for: {user_request}"})

    return steps
