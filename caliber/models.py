from __future__ import annotations

from typing import Dict, List

# Curated list of useful OpenRouter models. (free) ones are marked.
# Users can always use any OpenRouter model ID in custom mode.

MODEL_CATALOG: Dict[str, List[Dict[str, str]]] = {
    "planning": [
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "note": ""},
        {"id": "openai/o1", "name": "OpenAI o1", "note": ""},
        {"id": "openai/o1-mini", "name": "OpenAI o1-mini", "note": ""},
        {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 Flash", "note": ""},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B", "note": "(free)"},
    ],
    "reasoning": [
        {"id": "openai/o1", "name": "OpenAI o1", "note": ""},
        {"id": "openai/o1-mini", "name": "OpenAI o1-mini", "note": ""},
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "note": ""},
        {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1", "note": ""},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B", "note": "(free)"},
    ],
    "coding": [
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "note": ""},
        {"id": "openai/gpt-4o", "name": "GPT-4o", "note": ""},
        {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "note": ""},
        {"id": "qwen/qwen-2.5-coder-32b-instruct", "name": "Qwen2.5 Coder 32B", "note": ""},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B", "note": "(free)"},
    ],
    "search": [
        {"id": "perplexity/llama-3.1-sonar-large-128k-online", "name": "Sonar Large Online", "note": ""},
        {"id": "perplexity/llama-3.1-sonar-small-128k-online", "name": "Sonar Small Online", "note": ""},
        {"id": "openai/gpt-4o-mini", "name": "GPT-4o mini", "note": ""},
    ],
    "writing": [
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "note": ""},
        {"id": "openai/gpt-4o", "name": "GPT-4o", "note": ""},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B", "note": "(free)"},
    ],
    "default": [
        {"id": "openai/gpt-4o", "name": "GPT-4o", "note": ""},
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "note": ""},
        {"id": "openai/gpt-4o-mini", "name": "GPT-4o mini", "note": ""},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B", "note": "(free)"},
    ],
}

def list_models_for_task(task: str) -> List[Dict[str, str]]:
    return MODEL_CATALOG.get(task, MODEL_CATALOG["default"])
