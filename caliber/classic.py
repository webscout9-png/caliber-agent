"""Classic prompt UI — always visible, always works."""
from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .agent import CaliberAgent
from .config import CONFIG_DIR, get_api_key, load_config, save_config, set_api_key
from .models import fetch_all_models

console = Console()


def run_classic() -> None:
    console.print()
    console.print(f"[bold cyan]  CALIBER AGENT[/]  v{__version__}")
    console.print("[dim]  Multi-model coding agent · type /help[/]\n")

    agent = CaliberAgent()
    if not get_api_key():
        console.print("[yellow]  No API key yet. Run:[/]")
        console.print("  [bold]/provider sk-or-your-openrouter-key[/]\n")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    session = PromptSession(history=FileHistory(str(CONFIG_DIR / "history")))

    while True:
        cfg = load_config()
        bar = Text.assemble(
            (" caliber ", "bold cyan"),
            (f" mode:{cfg.get('mode', 'build')} ", "white"),
            (f" effort:{cfg.get('effort', 'medium')} ", "yellow"),
            (f" models:{cfg.get('model_mode', 'best')} ", "magenta"),
            (f" key:{'✓' if get_api_key() else '✗'} ", "green" if get_api_key() else "red"),
            (f" tokens:{agent.total_tokens} ", "dim"),
        )
        console.print(Panel(bar, border_style="dim", padding=(0, 0)))

        try:
            user_input = session.prompt("› ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye.[/]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            name = user_input.split()[0].lower()
            rest = user_input[len(name):].strip()
            if name in ("/exit", "/quit", "/q"):
                break
            if name == "/help":
                console.print(
                    "  /provider KEY   set OpenRouter key\n"
                    "  /plan           read-only mode\n"
                    "  /build          full tools mode\n"
                    "  /effort LEVEL   low|medium|high|max|ultra\n"
                    "  /model MODE     best|custom\n"
                    "  /models         list catalog\n"
                    "  /init           create AGENTS.md\n"
                    "  /status         show config\n"
                    "  /exit           quit\n"
                    "  caliberagent --tui   try full-screen UI"
                )
            elif name == "/provider":
                if rest:
                    set_api_key(rest)
                    console.print("[green]  Key saved.[/]")
                else:
                    console.print("  Usage: /provider sk-or-...")
            elif name == "/plan":
                cfg["mode"] = "plan"
                save_config(cfg)
                console.print("[cyan]  → plan[/]")
            elif name == "/build":
                cfg["mode"] = "build"
                save_config(cfg)
                console.print("[green]  → build[/]")
            elif name == "/effort" and rest in ("low", "medium", "high", "max", "ultra"):
                cfg["effort"] = rest
                save_config(cfg)
                console.print(f"[green]  → {rest}[/]")
            elif name == "/model" and rest in ("best", "custom"):
                cfg["model_mode"] = rest
                save_config(cfg)
                console.print(f"[green]  → {rest}[/]")
            elif name == "/status":
                console.print(f"  {cfg}")
            elif name == "/models":
                models = fetch_all_models()
                console.print(f"  {len(models)} models")
                for m in models[:20]:
                    console.print(f"    {m['id']} {m.get('note', '')}")
            elif name == "/init":
                try:
                    console.print(Panel(Markdown(agent.init_project()), title="AGENTS.md"))
                except Exception as e:
                    console.print(f"[red]  {e}[/]")
            else:
                console.print(f"[yellow]  Unknown: {name}[/]")
            continue

        try:
            result = agent.run(user_input)
            console.print()
            console.print(Panel(Markdown(result or "(empty)"), title="Caliber", border_style="cyan"))
            console.print()
        except Exception as e:
            console.print(f"[red]  Error: {e}[/]")
