from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Input, RichLog, Static

from . import __version__
from .agent import CaliberAgent
from .config import get_api_key, load_config, save_config, set_api_key


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


class CaliberApp(App):
    """Simple, responsive full-screen TUI for Caliber."""

    CSS = """
    Screen {
        background: #0d0d0f;
    }

    #header {
        dock: top;
        height: 3;
        background: #16161a;
        color: #e4e4e7;
        padding: 0 2;
        border-bottom: tall #2a2a30;
    }

    #header-title {
        text-style: bold;
        color: #7dd3fc;
    }

    #body {
        height: 1fr;
    }

    #log {
        width: 1fr;
        height: 1fr;
        background: #0d0d0f;
        border: solid #1f1f24;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }

    #side {
        width: 26;
        height: 1fr;
        background: #121216;
        border: solid #1f1f24;
        padding: 1 1;
        color: #a1a1aa;
    }

    #footer-input {
        dock: bottom;
        height: 3;
        background: #16161a;
        border-top: tall #2a2a30;
        padding: 0 1;
    }

    Input {
        background: #0d0d0f;
        border: solid #3f3f46;
        color: #fafafa;
        width: 1fr;
    }

    Input:focus {
        border: solid #38bdf8;
    }

    Footer {
        background: #16161a;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("ctrl+p", "toggle_mode", "Plan/Build", show=True),
    ]

    TITLE = "Caliber"
    busy: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.agent = CaliberAgent()

    def compose(self) -> ComposeResult:
        with Vertical(id="header"):
            yield Static(
                f"[bold #7dd3fc]CALIBER[/]  v{__version__}   "
                f"[dim]{Path.cwd()}[/]",
                id="header-title",
            )
            yield Static(self._status_line(), id="header-status")

        with Horizontal(id="body"):
            yield RichLog(id="log", markup=True, highlight=True, wrap=True, auto_scroll=True)
            yield Static(self._side_text(), id="side")

        with Horizontal(id="footer-input"):
            yield Input(placeholder="Message Caliber…  (/help for commands)", id="input")

        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[bold #7dd3fc]Caliber Agent[/] v{__version__}")
        log.write(f"[dim]Project: {Path.cwd()}[/]")
        log.write("")
        if not get_api_key():
            log.write("[yellow]No API key.[/] Type:  [bold]/provider sk-or-your-key[/]")
        else:
            log.write("[green]Ready.[/] Type a request or [bold]/help[/]")
        log.write("[dim]────────────────────────────────────────[/]")
        self.query_one("#input", Input).focus()

    def _status_line(self) -> str:
        cfg = load_config()
        key = "[green]key✓[/]" if get_api_key() else "[red]key✗[/]"
        return (
            f"mode=[bold]{cfg.get('mode', 'build')}[/]  "
            f"effort=[bold]{cfg.get('effort', 'medium')}[/]  "
            f"models=[bold]{cfg.get('model_mode', 'best')}[/]  "
            f"{key}  tokens=[bold]{self.agent.total_tokens}[/]"
        )

    def _side_text(self) -> str:
        cfg = load_config()
        lines = [
            "[bold #7dd3fc]SESSION[/]",
            f"mode    {cfg.get('mode')}",
            f"effort  {cfg.get('effort')}",
            f"models  {cfg.get('model_mode')}",
            f"tokens  {self.agent.total_tokens}",
            f"key     {'set' if get_api_key() else 'MISSING'}",
            "",
            "[bold #7dd3fc]COMMANDS[/]",
            "/provider  set key",
            "/plan      read-only",
            "/build     full tools",
            "/effort X  low…ultra",
            "/init      AGENTS.md",
            "/models    catalog",
            "/status",
            "/help",
            "/exit",
            "",
            "[bold #7dd3fc]KEYS[/]",
            "Ctrl+P  plan/build",
            "Ctrl+C  quit",
        ]
        if self.agent.last_trace:
            lines.append("")
            lines.append("[bold #7dd3fc]TRACE[/]")
            for s in self.agent.last_trace[-5:]:
                lines.append(f"{s['task'][:10]} {s['tokens']}t")
        return "\n".join(lines)

    def refresh_chrome(self) -> None:
        try:
            self.query_one("#header-status", Static).update(self._status_line())
            self.query_one("#side", Static).update(self._side_text())
        except Exception:
            pass

    @on(Input.Submitted, "#input")
    def handle_input(self, event: Input.Submitted) -> None:
        text = (event.value or "").strip()
        event.input.value = ""
        if not text:
            return
        if self.busy:
            self.query_one("#log", RichLog).write("[yellow]Busy — wait for current task[/]")
            return

        if text.startswith("/"):
            self.handle_command(text)
            return

        log = self.query_one("#log", RichLog)
        log.write("")
        log.write(f"[bold #86efac]you[/] [dim]{_ts()}[/]")
        log.write(text)
        log.write("")
        self.busy = True
        self.refresh_chrome()
        self.run_agent(text)

    @work(thread=True, exclusive=True)
    def run_agent(self, text: str) -> None:
        # Silence rich Progress in agent while TUI is active
        import caliber.agent as agent_mod
        from rich.console import Console

        quiet = Console(quiet=True)
        old = agent_mod.console
        agent_mod.console = quiet
        try:
            result = self.agent.run(text)
        except Exception as e:
            result = None
            err = str(e)
            self.call_from_thread(self._on_error, err)
            return
        finally:
            agent_mod.console = old

        self.call_from_thread(self._on_result, result or "(no output)")

    def _on_result(self, result: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[bold #7dd3fc]caliber[/] [dim]{_ts()}[/]")
        # Write result line by line for readability
        for line in (result or "").splitlines() or ["(empty)"]:
            log.write(line)
        log.write("[dim]────────────────────────────────────────[/]")
        self.busy = False
        self.refresh_chrome()
        self.query_one("#input", Input).focus()

    def _on_error(self, err: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[red]Error:[/] {err}")
        log.write("[dim]────────────────────────────────────────[/]")
        self.busy = False
        self.refresh_chrome()
        self.query_one("#input", Input).focus()

    def handle_command(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        parts = cmd.strip().split(maxsplit=1)
        name = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        cfg = load_config()

        if name in ("/exit", "/quit", "/q"):
            self.exit()
            return

        if name == "/help":
            log.write(
                "[bold]Commands[/]  /provider KEY  /plan  /build  "
                "/effort low|medium|high|max|ultra  /init  /models  /status  /exit"
            )
        elif name == "/provider":
            if rest:
                set_api_key(rest)
                log.write("[green]API key saved.[/]")
            else:
                log.write("Usage: [bold]/provider sk-or-...[/]")
        elif name == "/plan":
            cfg["mode"] = "plan"
            save_config(cfg)
            log.write("[cyan]→ Plan mode[/] (read-only)")
        elif name == "/build":
            cfg["mode"] = "build"
            save_config(cfg)
            log.write("[green]→ Build mode[/] (tools + bash)")
        elif name == "/effort":
            if rest in ("low", "medium", "high", "max", "ultra"):
                cfg["effort"] = rest
                save_config(cfg)
                log.write(f"[green]Effort → {rest}[/]")
            else:
                log.write("Usage: /effort low|medium|high|max|ultra")
        elif name == "/model":
            if rest in ("best", "custom"):
                cfg["model_mode"] = rest
                save_config(cfg)
                log.write(f"[green]Models → {rest}[/]")
            else:
                log.write("Usage: /model best|custom")
        elif name == "/status":
            log.write(self._status_line())
        elif name == "/usage":
            log.write(f"Tokens: {self.agent.total_tokens}")
        elif name == "/init":
            if not get_api_key():
                log.write("[yellow]Set /provider first[/]")
            else:
                self.busy = True
                self.run_init()
                return
        elif name == "/models":
            self.busy = True
            self.run_models()
            return
        else:
            log.write(f"[yellow]Unknown:[/] {name}  (/help)")

        self.refresh_chrome()

    @work(thread=True, exclusive=True)
    def run_init(self) -> None:
        try:
            result = self.agent.init_project()
            self.call_from_thread(self._on_result, result)
        except Exception as e:
            self.call_from_thread(self._on_error, str(e))

    @work(thread=True, exclusive=True)
    def run_models(self) -> None:
        from .models import fetch_all_models

        try:
            models = fetch_all_models()
            free = sum(1 for m in models if m.get("note") == "(free)")
            lines = [f"{len(models)} models ({free} free)"]
            for m in models[:20]:
                note = f" {m['note']}" if m.get("note") else ""
                lines.append(f"  {m['id']}{note}")
            lines.append("  …")
            self.call_from_thread(self._on_result, "\n".join(lines))
        except Exception as e:
            self.call_from_thread(self._on_error, str(e))

    def action_toggle_mode(self) -> None:
        cfg = load_config()
        cfg["mode"] = "plan" if cfg.get("mode") == "build" else "build"
        save_config(cfg)
        self.query_one("#log", RichLog).write(f"→ [bold]{cfg['mode']}[/] mode")
        self.refresh_chrome()


def run_tui() -> None:
    CaliberApp().run()
