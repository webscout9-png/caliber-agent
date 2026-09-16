# Caliber Agent

Multi-model coding agent for the terminal. Uses OpenRouter and routes each job to the best specialist model.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/webscout9-png/caliber-agent/main/scripts/install.sh | bash
```

```bash
caliberagent
```

Then set your key:

```
/provider sk-or-...
```

## Commands

| Command | What it does |
|---------|----------------|
| `/provider KEY` | Save OpenRouter API key |
| `/plan` | Read-only mode |
| `/build` | Full tools (edit, bash, …) |
| `/effort LEVEL` | `low` · `medium` · `high` · `max` · `ultra` |
| `/model MODE` | `best` or `custom` |
| `/models` | List OpenRouter catalog |
| `/init` | Create `AGENTS.md` for this project |
| `/status` | Show config |
| `/exit` | Quit |

## Modes

- **Plan** — analyze only (no writes / bash)
- **Build** — full agent loop with tools

## Specialist routing

Tasks are classified (coding, planning, reasoning, search, writing, critique) and each uses a different model when `model_mode=best`.

## UI

Default is the classic prompt (always works):

```bash
caliberagent
```

Optional full-screen TUI:

```bash
caliberagent --tui
```

## License

MIT · https://github.com/webscout9-png/caliber-agent
