# Caliber Agent

**The specialized multi-model OpenRouter terminal agent.**

Caliber does not force one expensive model for everything.  
It decomposes every request into precise sub-tasks and routes each one to the *best* model for that job (Claude for coding, strong reasoners for logic, online models for search, fast models for synthesis, etc.).

One OpenRouter API key. Higher quality. Lower cost.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/webscout9-png/caliber-agent/main/scripts/install.sh | bash
```

Or:

```bash
pip install git+https://github.com/webscout9-png/caliber-agent.git
```

Then:

```bash
caliberagent
```

## Core Philosophy

Most agents are generalists that overpay.  
Caliber is a **specialist orchestrator**:

1. Classifies the request
2. Decomposes it (simple heuristics for low effort, full LLM planner for high/max/ultra)
3. Routes every sub-task to the optimal model
4. Synthesizes a clean final answer

This produces better results than using Claude or GPT-4 for every single token.

## Commands

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `/provider` | Set your OpenRouter API key                      |
| `/model`    | Best (auto) or Custom model mapping per task     |
| `/effort`   | `low` · `medium` · `high` · `max` · `ultra`      |
| `/plan`     | Switch to Plan mode (plan only, no execution)    |
| `/build`    | Switch to Build mode (full execution)            |
| `/skills`   | Extensible skills system                         |
| `/usage`    | Token usage this session                         |
| `/sessions` | List saved sessions                              |
| `/status`   | Current configuration                            |
| `/exit`     | Quit                                             |

## Model Routing

**Best mode** (default): Caliber automatically selects strong models for each specialist role.

**Custom mode**: You map any OpenRouter model ID yourself. Free models are clearly marked `(free)` in the catalog.

## Effort Levels

- **low** — single specialist call  
- **medium** — plan → execute → light review  
- **high** — richer decomposition + review  
- **max** — full multi-step pipeline + synthesis  
- **ultra** — LLM planner + search + multiple specialist passes + rigorous synthesis

## Architecture (v0.2+)

- `router.py` — intelligent classification + effort-aware decomposition  
- LLM Planner (high/max/ultra) — uses a strong planning model to create real step graphs  
- Specialist roles: planning, reasoning, coding, search, writing, critique  
- Clean synthesis step so the user always receives one coherent answer  
- Persistent config in `~/.caliber/`

## License

MIT — fully open source.

---

**Repo**: https://github.com/webscout9-png/caliber-agent
