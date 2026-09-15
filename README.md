# Caliber Agent

**The specialized multi-model OpenRouter terminal agent.**

Caliber does not force one expensive model for everything.  
It decomposes every request into precise sub-tasks and routes each one to the *best* model for that job.

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

## Quick Start

1. `caliberagent`
2. `/provider` → paste your OpenRouter key
3. (optional) `/model` → choose **Best** or **Custom** (pick by number, no typing IDs)
4. (optional) `/effort` → low / medium / high / max / ultra
5. Just type your request

## Model Selection (v0.3)

`/model` → Custom now shows a **numbered list** for every specialist role.

You only type a number (1, 2, 3…). Never type long model IDs.

Free models are clearly marked `(free)`.

Current catalog (Sep 2026) includes:
- Claude Fable 5.1
- GPT-5.6 Luna / Sol
- DeepSeek V4 / V4.1 Flash
- Hy4 Preview
- GLM 5.3 / Flash
- Gemini 3.8 Flash
- MiMo V2.5
- Nemotron 3 Ultra (free)
- Sonar Pro (search)

## Commands

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `/provider` | Set your OpenRouter API key                      |
| `/model`    | Best (auto) or Custom (pick by number)           |
| `/effort`   | `low` · `medium` · `high` · `max` · `ultra`      |
| `/plan`     | Switch to Plan mode                              |
| `/build`    | Switch to Build mode                             |
| `/skills`   | Extensible skills system                         |
| `/usage`    | Token usage this session                         |
| `/sessions` | List saved sessions                              |
| `/status`   | Current config + last run trace                  |
| `/exit`     | Quit                                             |

## Architecture

- Specialist roles: planning · reasoning · coding · search · writing · critique
- Low/medium: fast heuristic decomposition
- High/max/ultra: LLM planner creates a real step graph
- Each step is routed to the best model for that specialist
- Final synthesis produces one clean answer

## License

MIT — fully open source.

**Repo**: https://github.com/webscout9-png/caliber-agent
