from __future__ import annotations

from typing import Dict, List

# Updated September 2026 — real OpenRouter usage leaders + strong specialists.
# Free models are explicitly marked (free).

MODEL_CATALOG: Dict[str, List[Dict[str, str]]] = {
    "planning": [
        {"id": "anthropic/claude-fable-5.1", "name": "Claude Fable 5.1", "note": ""},
        {"id": "openai/gpt-5.6-sol", "name": "GPT-5.6 Sol", "note": ""},
        {"id": "tencent/hy4-preview", "name": "Hy4 Preview", "note": ""},
        {"id": "deepseek/deepseek-v4.1-flash", "name": "DeepSeek V4.1 Flash", "note": ""},
        {"id": "z-ai/glm-5.3", "name": "GLM 5.3", "note": ""},
        {"id": "nvidia/nemotron-3-ultra", "name": "Nemotron 3 Ultra", "note": "(free)"},
    ],
    "reasoning": [
        {"id": "anthropic/claude-fable-5.1", "name": "Claude Fable 5.1", "note": ""},
        {"id": "openai/gpt-5.6-sol", "name": "GPT-5.6 Sol", "note": ""},
        {"id": "deepseek/deepseek-v4.1-flash", "name": "DeepSeek V4.1 Flash", "note": ""},
        {"id": "google/gemini-3.8-flash", "name": "Gemini 3.8 Flash", "note": ""},
        {"id": "z-ai/glm-5.3", "name": "GLM 5.3", "note": ""},
        {"id": "nvidia/nemotron-3-ultra", "name": "Nemotron 3 Ultra", "note": "(free)"},
    ],
    "coding": [
        {"id": "anthropic/claude-fable-5.1", "name": "Claude Fable 5.1", "note": ""},
        {"id": "tencent/hy4-preview", "name": "Hy4 Preview", "note": ""},
        {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek V4 Flash", "note": ""},
        {"id": "openai/gpt-5.6-luna", "name": "GPT-5.6 Luna", "note": ""},
        {"id": "z-ai/glm-5.3-flash", "name": "GLM 5.3 Flash", "note": ""},
        {"id": "nvidia/nemotron-3-ultra", "name": "Nemotron 3 Ultra", "note": "(free)"},
    ],
    "search": [
        {"id": "perplexity/sonar-pro", "name": "Sonar Pro", "note": ""},
        {"id": "perplexity/sonar", "name": "Sonar", "note": ""},
        {"id": "openai/gpt-5.6-luna", "name": "GPT-5.6 Luna", "note": ""},
        {"id": "google/gemini-3.8-flash", "name": "Gemini 3.8 Flash", "note": ""},
    ],
    "writing": [
        {"id": "anthropic/claude-fable-5.1", "name": "Claude Fable 5.1", "note": ""},
        {"id": "openai/gpt-5.6-luna", "name": "GPT-5.6 Luna", "note": ""},
        {"id": "google/gemini-3.8-flash", "name": "Gemini 3.8 Flash", "note": ""},
        {"id": "xiaomi/mimo-v2.5", "name": "MiMo V2.5", "note": ""},
        {"id": "nvidia/nemotron-3-ultra", "name": "Nemotron 3 Ultra", "note": "(free)"},
    ],
    "critique": [
        {"id": "anthropic/claude-fable-5.1", "name": "Claude Fable 5.1", "note": ""},
        {"id": "openai/gpt-5.6-sol", "name": "GPT-5.6 Sol", "note": ""},
        {"id": "deepseek/deepseek-v4.1-flash", "name": "DeepSeek V4.1 Flash", "note": ""},
        {"id": "z-ai/glm-5.3", "name": "GLM 5.3", "note": ""},
    ],
    "default": [
        {"id": "openai/gpt-5.6-luna", "name": "GPT-5.6 Luna", "note": ""},
        {"id": "anthropic/claude-fable-5.1", "name": "Claude Fable 5.1", "note": ""},
        {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek V4 Flash", "note": ""},
        {"id": "google/gemini-3.8-flash", "name": "Gemini 3.8 Flash", "note": ""},
        {"id": "nvidia/nemotron-3-ultra", "name": "Nemotron 3 Ultra", "note": "(free)"},
    ],
}

# Strong defaults used in "best" mode (current strong specialists)
BEST_DEFAULTS = {
    "planning": "anthropic/claude-fable-5.1",
    "reasoning": "openai/gpt-5.6-sol",
    "coding": "anthropic/claude-fable-5.1",
    "search": "perplexity/sonar-pro",
    "writing": "anthropic/claude-fable-5.1",
    "critique": "openai/gpt-5.6-sol",
    "default": "openai/gpt-5.6-luna",
}

def list_models_for_task(task: str) -> List[Dict[str, str]]:
    return MODEL_CATALOG.get(task, MODEL_CATALOG["default"])
