from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .models import BEST_DEFAULTS

CONFIG_DIR = Path.home() / ".caliber"
CONFIG_FILE = CONFIG_DIR / "config.json"
SESSIONS_DIR = CONFIG_DIR / "sessions"

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "openrouter",
    "api_key": None,
    "effort": "medium",
    "mode": "build",          # plan | build
    "model_mode": "best",     # best | custom
    "custom_models": {
        "planning": "anthropic/claude-3.5-sonnet",
        "reasoning": "openai/o1-mini",
        "coding": "anthropic/claude-3.5-sonnet",
        "search": "perplexity/llama-3.1-sonar-large-128k-online",
        "writing": "anthropic/claude-3.5-sonnet",
        "critique": "openai/o1-mini",
        "default": "openai/gpt-4o-mini",
    },
    "best_models": BEST_DEFAULTS.copy(),
}

def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> Dict[str, Any]:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    # ensure nested dicts exist
    for key in ("custom_models", "best_models"):
        if key not in merged or not isinstance(merged[key], dict):
            merged[key] = DEFAULT_CONFIG[key].copy()
        else:
            # fill missing specialist keys
            for k, v in DEFAULT_CONFIG[key].items():
                merged[key].setdefault(k, v)
    return merged

def save_config(cfg: Dict[str, Any]) -> None:
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def get_api_key() -> Optional[str]:
    cfg = load_config()
    return cfg.get("api_key")

def set_api_key(key: str) -> None:
    cfg = load_config()
    cfg["api_key"] = key.strip()
    save_config(cfg)
