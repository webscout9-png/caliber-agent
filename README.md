# Caliber Agent

**The multi-model OpenRouter terminal agent that actually routes every sub-task to the best model.**

Caliber breaks your request into small parts and hands each part to the optimal model (Claude for coding, strong reasoners for planning, fast/cheap models for search & simple steps, etc.). One OpenRouter key. Far better results at lower cost than using a single expensive model for everything.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/webscout9-png/caliber-agent/main/scripts/install.sh | bash
```

Or with pip:

```bash
pip install caliber-agent
```

Then run:

```bash
caliberagent
```

## Core Features

- **Single provider**: OpenRouter only (one API key → hundreds of models)
- **Best / Custom model routing**: `/model` → Best (auto-picks top model per task type) or Custom (you map models yourself)
- Free models clearly marked `(free)`
- Effort levels: `low` | `medium` | `high` | `max` | `ultra`
- Plan / Build mode switch
- Clean, fast terminal UI with live usage bar
- Commands: `/provider`, `/model`, `/effort`, `/plan`, `/build`, `/skills`, `/usage`, `/sessions`, `/status`, `/exit`
- Session persistence, skills system, token tracking

## Philosophy

Most agents force one model for everything. Caliber treats models as specialized tools. The result is higher quality *and* lower cost.

## License

MIT
