# Caliber Agent

**OpenCode-level coding agent + multi-model specialist routing.**

Caliber matches the best of OpenCode (Plan/Build, tools, AGENTS.md, agent loop) and goes further:

> **Different best models for different jobs** — planning, coding, critique, search — each on the optimal OpenRouter model.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/webscout9-png/caliber-agent/main/scripts/install.sh | bash
```

```bash
cd your-project
caliberagent
```

## vs OpenCode

| Capability | OpenCode | Caliber |
|------------|----------|---------|
| Plan / Build modes | Yes | Yes |
| File tools (read/write/edit/glob/grep) | Yes | Yes |
| Bash | Yes | Yes |
| Web fetch | Yes | Yes |
| `/init` → AGENTS.md | Yes | Yes |
| Agent tool loop | Yes | Yes |
| **Best model per specialist role** | Usually one model | **Core feature** |
| Live 200+ OpenRouter models | Via providers | **Native + free detection** |
| Effort levels low→ultra | — | Yes |

## Quick start

```bash
caliberagent
/provider          # OpenRouter key
/init              # create AGENTS.md for this repo
/build             # full agent
# or /plan for read-only
```

## Commands

| Command | Description |
|---------|-------------|
| `/provider` | OpenRouter API key |
| `/model` | Best or Custom (number + search) |
| `/models` | Full live catalog |
| `/effort` | low · medium · high · max · ultra |
| `/plan` | Read-only planning |
| `/build` | Full tools + edits + bash |
| `/init` | Generate AGENTS.md |
| `/status` | Config + last specialist trace |
| `/exit` | Quit |

## Architecture

1. Classify task → pick specialist model  
2. High+ effort → planning specialist first  
3. Agent loop with tools (permissions by mode)  
4. Max/ultra → critique specialist polish  

**Repo:** https://github.com/webscout9-png/caliber-agent  
**License:** MIT
