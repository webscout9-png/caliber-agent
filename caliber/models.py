from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

# Avoid circular import with config — define path locally
_CONFIG_DIR = Path.home() / ".caliber"
CACHE_FILE = _CONFIG_DIR / "models_cache.json"
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours

# Strong defaults for "best" mode
BEST_DEFAULTS = {
    "planning": "anthropic/claude-fable-5.1",
    "reasoning": "openai/gpt-5.6-sol",
    "coding": "anthropic/claude-fable-5.1",
    "search": "perplexity/sonar-pro",
    "writing": "anthropic/claude-fable-5.1",
    "critique": "openai/gpt-5.6-sol",
    "default": "openai/gpt-5.6-luna",
}

def _is_free(model: Dict[str, Any]) -> bool:
    pricing = model.get("pricing") or {}
    try:
        prompt = float(pricing.get("prompt") or "1")
        completion = float(pricing.get("completion") or "1")
        return prompt == 0.0 and completion == 0.0
    except (TypeError, ValueError):
        return False

def _normalize(model: Dict[str, Any]) -> Dict[str, str]:
    mid = model.get("id") or ""
    name = model.get("name") or mid
    free = _is_free(model)
    note = "(free)" if free else ""
    if mid.endswith(":free") or ":free" in mid:
        note = "(free)"
    return {"id": mid, "name": name, "note": note}

def fetch_all_models(force: bool = False) -> List[Dict[str, str]]:
    """Fetch every model from OpenRouter. Cache for 6h."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not force and CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if time.time() - cached.get("ts", 0) < CACHE_TTL_SECONDS:
                return cached.get("models", [])
        except Exception:
            pass

    models: List[Dict[str, str]] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get("https://openrouter.ai/api/v1/models")
            r.raise_for_status()
            data = r.json().get("data", [])

            for m in data:
                arch = m.get("architecture") or {}
                out_mods = arch.get("output_modalities") or ["text"]
                if "text" not in out_mods and out_mods != []:
                    continue
                norm = _normalize(m)
                if norm["id"]:
                    models.append(norm)

            models.sort(key=lambda x: (0 if x["note"] == "(free)" else 1, x["name"].lower()))

            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"ts": time.time(), "models": models}, f)

    except Exception:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("models", [])
            except Exception:
                pass
        return [
            {"id": "openai/gpt-5.6-luna", "name": "GPT-5.6 Luna", "note": ""},
            {"id": "anthropic/claude-fable-5.1", "name": "Claude Fable 5.1", "note": ""},
            {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek V4 Flash", "note": ""},
            {"id": "google/gemini-3.8-flash", "name": "Gemini 3.8 Flash", "note": ""},
            {"id": "nvidia/nemotron-3-ultra", "name": "Nemotron 3 Ultra", "note": "(free)"},
        ]

    return models

def search_models(query: str = "", limit: int = 50) -> List[Dict[str, str]]:
    all_models = fetch_all_models()
    if not query:
        return all_models[:limit]

    q = query.lower().strip()
    hits = []
    for m in all_models:
        if q in m["id"].lower() or q in m["name"].lower():
            hits.append(m)
            if len(hits) >= limit:
                break
    return hits

def list_models_for_task(task: str) -> List[Dict[str, str]]:
    all_models = fetch_all_models()
    keywords = {
        "coding": ["code", "coder", "claude", "deepseek", "gpt", "qwen", "hy4", "glm"],
        "reasoning": ["o1", "o3", "reason", "r1", "fable", "sol", "pro"],
        "planning": ["claude", "fable", "gpt", "sol", "gemini"],
        "search": ["sonar", "perplexity", "search", "online"],
        "writing": ["claude", "gpt", "gemini", "luna"],
        "critique": ["claude", "fable", "sol", "o1", "reason"],
        "default": [],
    }.get(task, [])

    scored = []
    for m in all_models:
        score = 0
        low = (m["id"] + " " + m["name"]).lower()
        for kw in keywords:
            if kw in low:
                score += 2
        if m["note"] == "(free)":
            score += 1
        scored.append((score, m))

    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:40]]
