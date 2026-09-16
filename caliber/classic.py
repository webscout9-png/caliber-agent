"""Classic prompt-toolkit UI (fallback when Textual is unavailable)."""
from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .agent import CaliberAgent
from .config import CONFIG_DIR, get_api_key, load_config, save_config, set_api_key
from .models import fetch_all_models, list_models_for_task, search_models

console = Console()


def run_classic() -> None:
    console.print(
        f"[bold cyan]Caliber Agent[/] v{__version__}  [dim](classic UI)[/]\n"
        "type /help · full TUI: pip install textual && caliberagent\n"
    )
    agent = CaliberAgent()
    if not get_api_key():
        console.print("[yellow]No API key. /provider sk-or-...[/]\n")

    history_file = CONFIG_DIR / "history"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    session = PromptSession(history=FileHistory(str(history_file)))

    while True:
        cfg = load_config()
        bar = Text.assemble(
            (" openrouter ", "bold"),
            (f" key:{'✓' if get_api_key() else '✗'} ", "green" if get_api_key() else "red"),
            (f" mode:{cfg.get('mode')} ", "cyan"),
            (f" effort:{cfg.get('effort')} ", "yellow"),
            (f" tokens:{agent.total_tokens} ", "dim"),
        )
        console.print(Panel(bar, border_style="dim", padding=(0, 1)))
        try:
            user_input = session.prompt("caliber › ").strip()
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
                console.print("/provider /plan /build /effort /model /models /init /status /exit")
            elif name == "/provider" and rest:
                set_api_key(rest)
                console.print("[green]Key saved.[/]")
            elif name == "/plan":
                cfg["mode"] = "plan"
                save_config(cfg)
                console.print("[cyan]→ plan[/]")
            elif name == "/build":
                cfg["mode"] = "build"
                save_config(cfg)
                console.print("[green]→ build[/]")
            elif name == "/effort" and rest in ("low", "medium", "high", "max", "ultra"):
                cfg["effort"] = rest
                save_config(cfg)
                console.print(f"[green]→ {rest}[/]")
            elif name == "/status":
                console.print(cfg)
            elif name == "/init":
                try:
                    console.print(Panel(Markdown(agent.init_project()), title="AGENTS.md"))
                except Exception as e:
                    console.print(f"[red]{e}[/]")
            elif name == "/models":
                models = fetch_all_models()
                console.print(f"{len(models)} models")
                for m in models[:15]:
                    console.print(f"  {m['id']} {m.get('note','')}")
            else:
                console.print(f"[yellow]{name}[/]")
            continue
        try:
            result = agent.run(user_input)
            console.print(Panel(Markdown(result), title="Caliber", border_style="cyan"))
        except Exception as e:
            console.print(f"[red]{e}[/]")
