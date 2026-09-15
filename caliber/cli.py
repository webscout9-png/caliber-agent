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
from .models import list_models_for_task

app = typer.Typer(add_completion=False, help="Caliber Agent — specialized multi-model OpenRouter terminal agent")
console = Console()

BANNER = r"""
   ____      _ _ _                
  / ___|__ _| (_) |__   ___ _ __  
 | |   / _` | | | '_ \ / _ \ '__| 
 | |__| (_| | | | |_) |  __/ |    
  \____\__,_|_|_|_.__/ \___|_|    
                                   
  Specialized multi-model · OpenRouter · Terminal
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
        (" openrouter ", "bold"),
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
    table.add_row("/provider", "Set OpenRouter API key (only provider)")
    table.add_row("/model", "Best (auto) or Custom — pick models by number")
    table.add_row("/effort", "low | medium | high | max | ultra")
    table.add_row("/plan", "Switch to Plan mode")
    table.add_row("/build", "Switch to Build mode")
    table.add_row("/skills", "Skills system (extensible)")
    table.add_row("/usage", "Token usage this session")
    table.add_row("/sessions", "List saved sessions")
    table.add_row("/status", "Show current config + last trace")
    table.add_row("/exit", "Quit")
    table.add_row("/help", "This help")
    console.print(table)

def cmd_provider() -> None:
    console.print("[bold]OpenRouter[/] is the only provider (one key → many specialist models).")
    key = console.input("[bold]Paste your OpenRouter API key: [/]").strip()
    if key:
        set_api_key(key)
        console.print("[green]API key saved to ~/.caliber/config.json[/]")
    else:
        console.print("[yellow]No key entered.[/]")

def _pick_model_by_number(task: str, current: str) -> str | None:
    """Show numbered list and let user pick by number. Returns model id or None."""
    models = list_models_for_task(task)
    console.print(f"\n[bold cyan]{task.upper()}[/]  (current: {current or '—'})")
    for i, m in enumerate(models, 1):
        note = f" [green]{m['note']}[/]" if m.get("note") else ""
        marker = " [bold]← current[/]" if m["id"] == current else ""
        console.print(f"  [bold]{i}[/]  {m['name']}{note}{marker}")
        console.print(f"      [dim]{m['id']}[/]")

    choice = console.input(f"  Pick number (1-{len(models)}) or Enter to keep: ").strip()
    if not choice:
        return None
    try:
        idx = int(choice)
        if 1 <= idx <= len(models):
            selected = models[idx - 1]
            console.print(f"  [green]→ {selected['name']}[/]")
            return selected["id"]
        else:
            console.print("[yellow]Invalid number.[/]")
            return None
    except ValueError:
        console.print("[yellow]Please enter a number.[/]")
        return None

def cmd_model() -> None:
    cfg = load_config()
    console.print("1) [bold]Best[/]  — Caliber auto-picks the strongest model for each specialist role")
    console.print("2) [bold]Custom[/] — You pick models by number (no typing IDs)")
    choice = console.input("Choice [1/2]: ").strip()

    if choice == "1":
        cfg["model_mode"] = "best"
        save_config(cfg)
        console.print("[green]Model mode → Best[/]")
        return

    if choice != "2":
        console.print("[yellow]Cancelled.[/]")
        return

    cfg["model_mode"] = "custom"
    console.print("\n[bold]Pick a model for each specialist role by number.[/]")
    console.print("Free models are marked [green](free)[/]. Press Enter to keep current.\n")

    for task in ["planning", "reasoning", "coding", "search", "writing", "critique", "default"]:
        current = cfg.get("custom_models", {}).get(task, "")
        selected = _pick_model_by_number(task, current)
        if selected:
            cfg.setdefault("custom_models", {})[task] = selected

    save_config(cfg)
    console.print("\n[green]Custom specialist mapping saved.[/]")

def cmd_effort() -> None:
    cfg = load_config()
    console.print("Effort: [bold]low[/] | medium | high | max | [bold]ultra[/]")
    console.print("  low   → single specialist call")
    console.print("  medium→ plan + execute + light review")
    console.print("  high  → LLM planner + richer pipeline")
    console.print("  max   → full multi-specialist + synthesis")
    console.print("  ultra → planner + search + multiple specialists + rigorous critique")
    val = console.input(f"Current [{cfg.get('effort')}] → ").strip().lower()
    if val in ("low", "medium", "high", "max", "ultra"):
        cfg["effort"] = val
        save_config(cfg)
        console.print(f"[green]Effort set to {val}[/]")
    else:
        console.print("[yellow]Invalid effort level.[/]")

def cmd_status(agent: CaliberAgent) -> None:
    cfg = load_config()
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="bold")
    table.add_column("Value")
    for k in ["provider", "effort", "mode", "model_mode"]:
        table.add_row(k, str(cfg.get(k)))
    table.add_row("api_key", "set ✓" if cfg.get("api_key") else "not set ✗")
    console.print(Panel(table, title="Config", border_style="dim"))

    if agent.last_trace:
        t = Table(title="Last run trace")
        t.add_column("Specialist")
        t.add_column("Model")
        t.add_column("Tokens", justify="right")
        for step in agent.last_trace:
            t.add_row(step["task"], step["model"], str(step["tokens"]))
        console.print(t)

def cmd_usage(agent: CaliberAgent) -> None:
    console.print(f"Session tokens: [bold]{agent.total_tokens}[/]")

def cmd_sessions() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SESSIONS_DIR.glob("*.json"))
    if not files:
        console.print("No sessions yet.")
        return
    for f in files:
        console.print(f"  · {f.stem}")

def cmd_skills() -> None:
    console.print("[bold]Built-in specialists[/]")
    console.print("  planning · reasoning · coding · search · writing · critique")
    console.print("\nThe router + LLM planner already specialize every request.")
    console.print("Future versions will support user-defined skills and tools.")

def handle_command(cmd: str, agent: CaliberAgent) -> bool:
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
        console.print("[cyan]→ Plan mode[/]")
    elif name == "/build":
        cfg = load_config()
        cfg["mode"] = "build"
        save_config(cfg)
        console.print("[green]→ Build mode[/]")
    elif name == "/skills":
        cmd_skills()
    elif name == "/usage":
        cmd_usage(agent)
    elif name == "/sessions":
        cmd_sessions()
    elif name == "/status":
        cmd_status(agent)
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

        try:
            result = agent.run(user_input)
            console.print()
            console.print(Panel(Markdown(result), title="Caliber", border_style="cyan"))
            console.print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")

if __name__ == "__main__":
    app()
