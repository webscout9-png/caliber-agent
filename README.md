# Caliber Agent

**The specialized multi-model OpenRouter terminal agent.**

Caliber decomposes every request into specialist sub-tasks and routes each one to the best model.  
One OpenRouter key → access to **every** model on OpenRouter (200+).

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/webscout9-png/caliber-agent/main/scripts/install.sh | bash
```

```bash
caliberagent
```

## Quick Start

1. `/provider` → paste OpenRouter API key
2. `/model` → Best (auto) or Custom (pick live models by number / search)
3. `/models` → browse or search the **full live catalog** (hundreds of models)
4. Type your request

## Live Model Catalog (v0.4)

- Fetches **all** text models directly from OpenRouter API
- Cached for 6 hours
- Free models automatically marked `(free)`
- `/models` → search the entire catalog
- `/model` → Custom shows smart shortlists + full search (just type a number or a search term)

You never have to type long model IDs.

## Commands

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `/provider` | Set OpenRouter API key                           |
| `/model`    | Best or Custom (number + search picker)          |
| `/models`   | Browse / search every OpenRouter model           |
| `/effort`   | low · medium · high · max · ultra                |
| `/plan`     | Plan mode                                        |
| `/build`    | Build mode                                       |
| `/status`   | Config + last run trace                          |
| `/usage`    | Tokens used                                      |
| `/exit`     | Quit                                             |

## Architecture

Specialist roles: planning · reasoning · coding · search · writing · critique  
Low/medium effort = fast heuristics  
High/max/ultra = LLM planner creates real step graphs  
Final synthesis always returns one clean answer

## License

MIT

**https://github.com/webscout9-png/caliber-agent**
