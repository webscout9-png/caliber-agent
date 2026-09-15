# Caliber Agent

**The specialized multi-model OpenRouter coding agent.**

Caliber is a full terminal coding agent (inspired by the best of OpenCode) with one unique superpower:

> **Different best models for different tasks.**

Planning → strong planner model  
Coding → best coding model  
Reasoning / critique → strong reasoners  
Search → online models  

One OpenRouter key. Live catalog of 200+ models. Higher quality at lower cost.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/webscout9-png/caliber-agent/main/scripts/install.sh | bash
```

```bash
caliberagent
```

## What makes it different

| Feature | Caliber |
|---------|--------|
| Multi-model specialist routing | **Core** — best model per role |
| Live OpenRouter catalog (200+) | Yes |
| Plan / Build modes | Yes |
| File tools (read/write/list/grep) | Yes |
| Bash tool | Yes (Build mode) |
| Project awareness (AGENTS.md) | Yes |
| Agent tool loop | Yes |
| Effort levels (low→ultra) | Yes |
| Free model detection | Yes |

## Quick Start

1. `/provider` → paste OpenRouter key
2. `/model` → Best or Custom (search + number picker)
3. `/plan` or `/build`
4. Work on a real project — Caliber reads/writes files and can run commands

Optional: create an `AGENTS.md` in your repo root so Caliber understands your conventions (same idea as OpenCode).

## Commands

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `/provider` | Set OpenRouter API key                           |
| `/model`    | Best or Custom (live catalog, number + search)   |
| `/models`   | Browse / search every OpenRouter model           |
| `/effort`   | low · medium · high · max · ultra                |
| `/plan`     | Read-only planning mode                          |
| `/build`    | Full agent with tools + edits + bash             |
| `/status`   | Config + last run trace                          |
| `/usage`    | Tokens                                           |
| `/exit`     | Quit                                             |

## Architecture (v0.5)

1. **Classify** the request
2. **Plan** with a specialist planning model (high+)
3. **Execute** with the best model for the task + full tool loop
4. **Critique** on max/ultra for final polish
5. Tools: `list_dir`, `read_file`, `write_file`, `grep`, `bash`

This is OpenCode-level agency + Caliber’s unique multi-model routing.

## License

MIT

**https://github.com/webscout9-png/caliber-agent**
