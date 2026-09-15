from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .config import load_config
from .models import BEST_DEFAULTS, list_models_for_task
from .openrouter import chat

TASK_KEYWORDS = {
    "coding": [
        "code", "implement", "function", "class", "bug", "fix", "refactor",
        "script", "program", "python", "javascript", "typescript", "api",
        "debug", "test", "unit test", "write a", "create a function",
        "algorithm", "data structure", "optimize", "performance",
    ],
    "reasoning": [
        "reason", "think", "analyze", "why", "logic", "prove", "deduce",
        "infer", "compare", "evaluate", "trade-off", "pros and cons",
        "what if", "implications", "cause", "effect",
    ],
    "planning": [
        "plan", "strategy", "steps", "roadmap", "architecture", "design",
        "outline", "break down", "how should I", "approach", "structure",
    ],
    "search": [
        "search", "find", "lookup", "current", "latest", "news", "web",
        "up to date", "recent", "what is the", "who is", "when did",
    ],
    "writing": [
        "write", "draft", "email", "blog", "article", "story", "documentation",
        "rewrite", "summarize", "explain", "describe", "report",
    ],
}

def classify_task(text: str) -> str:
    lower = text.lower()
    scores: Dict[str, int] = {k: 0 for k in TASK_KEYWORDS}
    for task, kws in TASK_KEYWORDS.items():
        for kw in kws:
            if kw in lower:
                scores[task] += 1 + (1 if len(kw) > 6 else 0)  # prefer longer phrases
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "default"
    return best

def get_model_for_task(task: str) -> str:
    cfg = load_config()
    if cfg.get("model_mode") == "custom":
        custom = cfg.get("custom_models", {})
        return custom.get(task) or custom.get("default") or BEST_DEFAULTS.get("default", "openai/gpt-4o-mini")
    # best mode
    best = cfg.get("best_models", {})
    return best.get(task) or BEST_DEFAULTS.get(task) or BEST_DEFAULTS.get("default", "openai/gpt-4o")

def _heuristic_decompose(user_request: str, effort: str, primary_task: str) -> List[Dict[str, str]]:
    """Fast, deterministic decomposition used for low/medium effort."""
    if effort == "low":
        return [{"type": primary_task, "instruction": user_request}]

    if effort in ("medium", "high"):
        if primary_task == "coding":
            return [
                {"type": "planning", "instruction": f"Design a clean architecture and step-by-step plan for: {user_request}"},
                {"type": "coding", "instruction": f"Implement the full solution. Original request: {user_request}"},
                {"type": "critique", "instruction": "Review the code rigorously: correctness, edge cases, simplicity, performance. Suggest concrete improvements."},
            ]
        if primary_task == "planning":
            return [
                {"type": "planning", "instruction": user_request},
                {"type": "critique", "instruction": "Critique the plan for gaps, risks, and missing steps. Improve it."},
            ]
        if primary_task == "reasoning":
            return [
                {"type": "reasoning", "instruction": user_request},
                {"type": "critique", "instruction": "Stress-test the reasoning. Point out weak links and refine the conclusion."},
            ]
        # generic
        return [
            {"type": primary_task, "instruction": user_request},
            {"type": "critique", "instruction": "Review and improve the previous output for accuracy, clarity and completeness."},
        ]

    # max / ultra fall through to richer pipeline
    steps = [
        {"type": "planning", "instruction": f"Produce a precise multi-step plan to fully solve: {user_request}"},
        {"type": "reasoning", "instruction": "Identify risks, edge cases, assumptions and success criteria."},
        {"type": primary_task if primary_task != "default" else "default", "instruction": f"Execute the core work for: {user_request}"},
        {"type": "critique", "instruction": "Critically review everything produced so far. List concrete improvements."},
        {"type": "writing", "instruction": "Synthesize a single clear, complete final answer for the user."},
    ]
    if effort == "ultra":
        steps.insert(2, {"type": "search", "instruction": f"Gather any missing current information required to solve: {user_request}"})
    return steps

def _llm_plan(user_request: str, effort: str) -> List[Dict[str, str]]:
    """Use a strong planning model to create a real step graph."""
    planner_model = get_model_for_task("planning")

    system = """You are the Planner component of Caliber Agent.
Your only job is to break the user request into a short sequence of specialist steps.

Available specialist types (use ONLY these):
- planning
- reasoning
- coding
- search
- writing
- critique
- default

Return STRICT JSON only, no markdown, no explanation:
{
  "steps": [
    {"type": "one_of_the_types_above", "instruction": "precise instruction for that specialist"},
    ...
  ]
}

Rules:
- 2–6 steps maximum.
- Be extremely precise in each instruction.
- Prefer specialist types that match the actual work needed.
- Always end with a critique or writing step if the request is complex.
- For coding tasks always include planning + coding + critique.
"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Effort level: {effort}\n\nUser request:\n{user_request}"},
    ]

    try:
        result = chat(planner_model, messages, temperature=0.2, max_tokens=1200)
        content = result["content"].strip()
        # extract JSON even if the model wraps it
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            steps = data.get("steps", [])
            cleaned = []
            for s in steps:
                t = s.get("type", "default")
                if t not in ("planning", "reasoning", "coding", "search", "writing", "critique", "default"):
                    t = "default"
                instr = s.get("instruction", "").strip()
                if instr:
                    cleaned.append({"type": t, "instruction": instr})
            if cleaned:
                return cleaned
    except Exception:
        pass

    # fallback
    return _heuristic_decompose(user_request, effort, classify_task(user_request))

def decompose(user_request: str, effort: str) -> List[Dict[str, str]]:
    """Main entry. Uses LLM planner on high+ effort for maximum specialization."""
    primary = classify_task(user_request)

    if effort in ("high", "max", "ultra"):
        return _llm_plan(user_request, effort)

    return _heuristic_decompose(user_request, effort, primary)
