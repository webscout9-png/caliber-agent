# Caliber Agent

**Full-screen multi-model coding agent** (OpenCode-style TUI + specialist routing).

When you run `caliberagent`, a real terminal UI opens — chat panel, sidebar, status bar, input — not a plain prompt.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/webscout9-png/caliber-agent/main/scripts/install.sh | bash
```

```bash
caliberagent
```

## UI

```
┌─ CALIBER v0.7  mode:build  effort:medium  tokens:0 ─────────────┐
│ Chat messages (markdown)              │ Session                 │
│                                       │ mode / effort / models  │
│                                       │ Last trace              │
│                                       │ Commands                │
├───────────────────────────────────────┴─────────────────────────┤
│ Ask Caliber…  (/ for commands)                                  │
└─────────────────────────────────────────────────────────────────┘
```

- **Ctrl+P** — toggle Plan / Build  
- **Ctrl+C** — quit  
- **F1** — help  
- Slash commands: `/provider`, `/plan`, `/build`, `/effort`, `/init`, `/models`, …

## Why Caliber

| Feature | Caliber |
|---------|--------|
| Full-screen TUI | Yes (Textual) |
| Plan / Build modes | Yes |
| File tools + bash | Yes |
| `/init` → AGENTS.md | Yes |
| **Best model per specialist** | **Core** |
| Live OpenRouter catalog (400+) | Yes |

## License

MIT · https://github.com/webscout9-png/caliber-agent
