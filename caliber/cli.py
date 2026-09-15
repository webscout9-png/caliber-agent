from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

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
from .models import list_models_for_task

app = typer.Typer(add_completion=False, help="Caliber Agent — multi-model OpenRouter terminal agent")
console = Console()

BANNER = r"""
   ____      _ _ _                
  / ___|__ _| (_) |__   ___ _ __  
 | |   / _` | | | '_ \ / _ \ '__| 
 | |__| (_| | | | |_) |  __/ |    
  \____\__,_|_|_|_.__/ \___|_|    
                                   
  Multi-model · OpenRouter · Terminal
"""

def print_banner() -> None:
    console.print(BANNER, style="bold cyan")
    console.print(f"  v{__version__}  ·  type /help for commands\n", style="dim")

def print_status_bar(agent: CaliberAgent) -> None:
    cfg = load_config()
    key_set = "✓" if get_api_key() else "✗"
    usage = f"tokens: {agent.total_tokens}"
    mode = cfg.get("mode", "build")
    effort = cfg.get("effort", "medium")
    model_mode = cfg.get("model_mode", "best")
    bar = Text.assemble(
        (" provider: openrouter ", "bold"),
        (f" key:{key_set} ", "green" if key_set == "✓" else "red"),
        (f" mode:{mode} ", "cyan"),
        (f" effort:{effort} ", "yellow"),
        (f" models:{model_mode} ", "magenta"),
        (f" {usage} ", "dim"),
    )
    console.print(Panel(bar, border_style="dim", padding=(0, 1)))

def cmd_help() -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Command")
    table.add_column("Description")
    table.add_row("/provider", "Set OpenRouter API key")
    table.add_row("/model", "Best (auto) or Custom model mapping")
    table.add_row("/effort", "low | medium | high | max | ultra")
    table.add_row("/plan", "Switch to Plan mode")
    table.add_row("/build", "Switch to Build mode")
    table.add_row("/skills", "List available skills (extensible)")
    table.add_row("/usage", "Show token usage")
    table.add_row("/sessions", "List saved sessions")
    table.add_row("/status", "Show current config")
    table.add_row("/exit  or  /quit", "Exit Caliber")
    table.add_row("/help", "This help")
    console.print(table)

def cmd_provider() -> None:
    console.print("OpenRouter is the only supported provider (one key → many models).")
    key = console.input("[bold]Paste your OpenRouter API key: [/]").strip()
    if key:
        set_api_key(key)
        console.print("[green]API key saved.[/]")
    else:
        console.print("[yellow]No key entered.[/]")

def cmd_model() -> None:
    cfg = load_config()
    console.print("1) Best  — Caliber picks the top model for each task type")
    console.print("2) Custom — You choose models per task")
    choice = console.input("Choice [1/2]: ").strip()
    if choice == "1":
        cfg["model_mode"] = "best"
        save_config(cfg)
        console.print("[green]Model mode set to Best.[/]")
    elif choice == "2":
        cfg["model_mode"] = "custom"
        console.print("Enter model IDs for each task (leave blank to keep current). Free models are marked (free) in the catalog.")
        for task in ["planning", "reasoning", "coding", "search", "writing", "default"]:
            current = cfg.get("custom_models", {}).get(task, "")
            models = list_models_for_task(task)
            console.print(f"\n[bold]{task}[/] (current: {current})")
            for m in models:
                note = f" {m['note']}" if m.get("note") else ""
                console.print(f"  · {m['id']}{note}")
            new = console.input(f"  New model for {task}: ").strip()
            if new:
                cfg.setdefault("custom_models", {})[task] = new
        save_config(cfg)
        console.print("[green]Custom models saved.[/]")
    else:
        console.print("[yellow]Cancelled.[/]")

def cmd_effort() -> None:
    cfg = load_config()
    console.print("Effort levels: low | medium | high | max | ultra")
    val = console.input(f"Current: {cfg.get('effort')} → ").strip().lower()
    if val in ("low", "medium", "high", "max", "ultra"):
        cfg["effort"] = val
        save_config(cfg)
        console.print(f"[green]Effort set to {val}.[/]")
    else:
        console.print("[yellow]Invalid effort.[/]")

def cmd_status() -> None:
    cfg = load_config()
    table = Table(show_header=False)
    table.add_column("Key", style="bold")
    table.add_column("Value")
    for k in ["provider", "effort", "mode", "model_mode"]:
        table.add_row(k, str(cfg.get(k)))
    table.add_row("api_key", "set" if cfg.get("api_key") else "not set")
    console.print(Panel(table, title="Status"))

def cmd_usage(agent: CaliberAgent) -> None:
    console.print(f"Session tokens used: [bold]{agent.total_tokens}[/]")

def cmd_sessions() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SESSIONS_DIR.glob("*.json"))
    if not files:
        console.print("No sessions yet.")
        return
    for f in files:
        console.print(f"  · {f.stem}")

def cmd_skills() -> None:
    console.print("Skills system is extensible. Built-in: task decomposition + model routing.")
    console.print("Future: custom skills, tools, MCP, etc.")

def handle_command(cmd: str, agent: CaliberAgent) -> bool:
    """Return True if should continue loop."""
    parts = cmd.strip().split(maxsplit=1)
    name = parts[0].lower()

    if name in ("/exit", "/quit", "/q"):
        console.print("[dim]Goodbye.[/]")
        return False
    if name == "/help":
        cmd_help()
    elif name == "/provider":
        cmd_provider()
    elif name == "/model":
        cmd_model()
    elif name == "/effort":
        cmd_effort()
    elif name == "/plan":
        cfg = load_config()
        cfg["mode"] = "plan"
        save_config(cfg)
        console.print("[cyan]Switched to Plan mode.[/]")
    elif name == "/build":
        cfg = load_config()
        cfg["mode"] = "build"
        save_config(cfg)
        console.print("[green]Switched to Build mode.[/]")
    elif name == "/skills":
        cmd_skills()
    elif name == "/usage":
        cmd_usage(agent)
    elif name == "/sessions":
        cmd_sessions()
    elif name == "/status":
        cmd_status()
    else:
        console.print(f"[yellow]Unknown command: {name}. Try /help[/]")
    return True

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    print_banner()
    agent = CaliberAgent()

    if not get_api_key():
        console.print("[yellow]No API key found. Run /provider to add your OpenRouter key.[/]\n")

    history_file = CONFIG_DIR / "history"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    session = PromptSession(history=FileHistory(str(history_file)))

    while True:
        print_status_bar(agent)
        try:
            user_input = session.prompt("caliber › ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            if not handle_command(user_input, agent):
                break
            continue

        # Normal request
        try:
            result = agent.run(user_input)
            console.print()
            console.print(Panel(Markdown(result), title="Caliber", border_style="cyan"))
            console.print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")

if __name__ == "__main__":
    app()
