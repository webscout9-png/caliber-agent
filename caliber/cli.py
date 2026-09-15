from __future__ import annotations

from pathlib import Path

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .agent import CaliberAgent
from .config import (
    CONFIG_DIR,
    SESSIONS_DIR,
    get_api_key,
    load_config,
    save_config,
    set_api_key,
)
from .models import fetch_all_models, list_models_for_task, search_models

app = typer.Typer(add_completion=False, help="Caliber Agent — multi-model coding agent")
console = Console()

BANNER = r"""
   ____      _ _ _                
  / ___|__ _| (_) |__   ___ _ __  
 | |   / _` | | | '_ \ / _ \ '__| 
 | |__| (_| | | | |_) |  __/ |    
  \____\__,_|_|_|_.__/ \___|_|    
                                   
  Multi-model coding agent · OpenRouter · Terminal
"""

def print_banner() -> None:
    console.print(BANNER, style="bold cyan")
    console.print(f"  v{__version__}  ·  /help for commands\n", style="dim")

def print_status_bar(agent: CaliberAgent) -> None:
    cfg = load_config()
    key_set = "✓" if get_api_key() else "✗"
    bar = Text.assemble(
        (" openrouter ", "bold"),
        (f" key:{key_set} ", "green" if key_set == "✓" else "red"),
        (f" mode:{cfg.get('mode', 'build')} ", "cyan"),
        (f" effort:{cfg.get('effort', 'medium')} ", "yellow"),
        (f" models:{cfg.get('model_mode', 'best')} ", "magenta"),
        (f" tokens:{agent.total_tokens} ", "dim"),
    )
    console.print(Panel(bar, border_style="dim", padding=(0, 1)))

def cmd_help() -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Command")
    table.add_column("Description")
    rows = [
        ("/provider", "Set OpenRouter API key"),
        ("/model", "Best or Custom (live catalog, number + search)"),
        ("/models", "Browse / search all OpenRouter models"),
        ("/effort", "low | medium | high | max | ultra"),
        ("/plan", "Plan mode — read-only analysis"),
        ("/build", "Build mode — full tools + edits + bash"),
        ("/init", "Analyze project and create AGENTS.md"),
        ("/skills", "Specialist roles overview"),
        ("/usage", "Token usage"),
        ("/sessions", "List sessions"),
        ("/status", "Config + last trace"),
        ("/exit", "Quit"),
    ]
    for a, b in rows:
        table.add_row(a, b)
    console.print(table)

def cmd_provider() -> None:
    console.print("[bold]OpenRouter[/] — one key, every model.")
    key = console.input("[bold]API key: [/]").strip()
    if key:
        set_api_key(key)
        console.print("[green]Saved.[/]")
    else:
        console.print("[yellow]Cancelled.[/]")

def cmd_models_browse() -> None:
    console.print("[dim]Fetching catalog...[/]")
    all_models = fetch_all_models()
    console.print(f"[green]{len(all_models)} models[/]\n")
    query = console.input("Search (Enter = first 40): ").strip()
    results = search_models(query, limit=60) if query else all_models[:40]
    for i, m in enumerate(results, 1):
        note = f" [green]{m['note']}[/]" if m.get("note") else ""
        console.print(f"  [bold]{i:3d}[/]  {m['name']}{note}")
        console.print(f"       [dim]{m['id']}[/]")

def _pick_from_list(models: list, current: str, title: str) -> str | None:
    console.print(f"\n[bold cyan]{title}[/]  (current: {current or '—'})")
    for i, m in enumerate(models, 1):
        note = f" [green]{m['note']}[/]" if m.get("note") else ""
        marker = " [bold]←[/]" if m["id"] == current else ""
        console.print(f"  [bold]{i:2d}[/]  {m['name']}{note}{marker}")
        console.print(f"      [dim]{m['id']}[/]")
    choice = console.input(f"  Number, search term, or Enter: ").strip()
    if not choice:
        return None
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(models):
            console.print(f"  [green]→ {models[idx-1]['name']}[/]")
            return models[idx - 1]["id"]
        console.print("[yellow]Invalid.[/]")
        return None
    hits = search_models(choice, limit=25)
    if not hits:
        console.print("[yellow]No matches.[/]")
        return None
    return _pick_from_list(hits, current, f"Search: {choice}")

def cmd_model() -> None:
    cfg = load_config()
    console.print("1) [bold]Best[/] — auto specialist models")
    console.print("2) [bold]Custom[/] — pick from live catalog")
    choice = console.input("Choice [1/2]: ").strip()
    if choice == "1":
        cfg["model_mode"] = "best"
        save_config(cfg)
        console.print("[green]→ Best[/]")
        return
    if choice != "2":
        console.print("[yellow]Cancelled.[/]")
        return
    cfg["model_mode"] = "custom"
    console.print("[dim]Loading models...[/]")
    fetch_all_models()
    for task in ["planning", "reasoning", "coding", "search", "writing", "critique", "default"]:
        current = cfg.get("custom_models", {}).get(task, "")
        selected = _pick_from_list(list_models_for_task(task), current, task.upper())
        if selected:
            cfg.setdefault("custom_models", {})[task] = selected
    save_config(cfg)
    console.print("[green]Saved.[/]")

def cmd_effort() -> None:
    cfg = load_config()
    console.print("low · medium · high · max · ultra")
    val = console.input(f"[{cfg.get('effort')}] → ").strip().lower()
    if val in ("low", "medium", "high", "max", "ultra"):
        cfg["effort"] = val
        save_config(cfg)
        console.print(f"[green]→ {val}[/]")
    else:
        console.print("[yellow]Invalid.[/]")

def cmd_status(agent: CaliberAgent) -> None:
    cfg = load_config()
    table = Table(show_header=False, box=None)
    table.add_column("K", style="bold")
    table.add_column("V")
    for k in ["provider", "effort", "mode", "model_mode"]:
        table.add_row(k, str(cfg.get(k)))
    table.add_row("api_key", "set" if cfg.get("api_key") else "missing")
    console.print(Panel(table, title="Status", border_style="dim"))
    if agent.last_trace:
        t = Table(title="Last trace")
        t.add_column("Role")
        t.add_column("Model")
        t.add_column("Tok", justify="right")
        for s in agent.last_trace:
            t.add_row(s["task"], s["model"], str(s["tokens"]))
        console.print(t)

def handle_command(cmd: str, agent: CaliberAgent) -> bool:
    name = cmd.strip().split(maxsplit=1)[0].lower()
    if name in ("/exit", "/quit", "/q"):
        console.print("[dim]Bye.[/]")
        return False
    if name == "/help":
        cmd_help()
    elif name == "/provider":
        cmd_provider()
    elif name == "/model":
        cmd_model()
    elif name == "/models":
        cmd_models_browse()
    elif name == "/effort":
        cmd_effort()
    elif name == "/plan":
        cfg = load_config()
        cfg["mode"] = "plan"
        save_config(cfg)
        console.print("[cyan]→ Plan mode (read-only)[/]")
    elif name == "/build":
        cfg = load_config()
        cfg["mode"] = "build"
        save_config(cfg)
        console.print("[green]→ Build mode (full tools)[/]")
    elif name == "/init":
        try:
            result = agent.init_project()
            console.print(Panel(Markdown(result), title="AGENTS.md", border_style="green"))
        except Exception as e:
            console.print(f"[red]{e}[/]")
    elif name == "/skills":
        console.print("Specialists: planning · reasoning · coding · search · writing · critique")
        console.print("Each can use a different OpenRouter model (Best or Custom).")
    elif name == "/usage":
        console.print(f"Tokens: [bold]{agent.total_tokens}[/]")
    elif name == "/sessions":
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(SESSIONS_DIR.glob("*.json"))
        console.print("\n".join(f"  · {f.stem}" for f in files) or "No sessions.")
    elif name == "/status":
        cmd_status(agent)
    else:
        console.print(f"[yellow]Unknown: {name}  (/help)[/]")
    return True

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return
    print_banner()
    agent = CaliberAgent()
    if not get_api_key():
        console.print("[yellow]No key. /provider to add OpenRouter key.[/]\n")
    history_file = CONFIG_DIR / "history"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    session = PromptSession(history=FileHistory(str(history_file)))
    while True:
        print_status_bar(agent)
        try:
            user_input = session.prompt("caliber › ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye.[/]")
            break
        if not user_input:
            continue
        if user_input.startswith("/"):
            if not handle_command(user_input, agent):
                break
            continue
        try:
            result = agent.run(user_input)
            console.print()
            console.print(Panel(Markdown(result), title="Caliber", border_style="cyan"))
            console.print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")

if __name__ == "__main__":
    app()
