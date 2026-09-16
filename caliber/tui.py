from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Input, RichLog, Static

from . import __version__
from .agent import CaliberAgent
from .config import get_api_key, load_config, save_config, set_api_key


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


class CaliberApp(App):
    """Minimal reliable TUI — log on top, input always at bottom."""

    # Pure vertical stack: header | log | status | input
    # No Footer widget (it was stealing space / hiding the prompt)
    CSS = """
    Screen {
        layout: vertical;
        background: #0d0d0f;
    }

    #top {
        height: 2;
        background: #1a1a1e;
        color: #e4e4e7;
        padding: 0 1;
        border-bottom: solid #333;
    }

    #log {
        height: 1fr;
        min-height: 5;
        background: #0d0d0f;
        border: solid #222;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }

    #status {
        height: 1;
        background: #1a1a1e;
        color: #a1a1aa;
        padding: 0 1;
        border-top: solid #333;
    }

    #input {
        height: 3;
        background: #0d0d0f;
        border: tall #38bdf8;
        color: #fafafa;
        margin: 0 0;
        padding: 0 1;
    }

    #input:focus {
        border: tall #7dd3fc;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "toggle_mode", "Plan/Build"),
        Binding("escape", "focus_input", "Focus"),
    ]

    TITLE = "Caliber"
    busy: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.agent = CaliberAgent()

    def compose(self) -> ComposeResult:
        yield Static(self._header_text(), id="top")
        yield RichLog(id="log", markup=True, wrap=True, auto_scroll=True, max_lines=2000)
        yield Static(self._status_text(), id="status")
        yield Input(
            placeholder="Type here and press Enter…   /help  /provider  /plan  /build",
            id="input",
        )

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[bold cyan]Caliber Agent[/] v{__version__}")
        log.write(f"[dim]{Path.cwd()}[/]")
        log.write("")
        if not get_api_key():
            log.write("[yellow]No API key.[/] Type:")
            log.write("  [bold]/provider sk-or-your-key[/]")
        else:
            log.write("[green]Ready.[/] Type a message below and press Enter.")
        log.write("[dim]─────────────────────────────────────[/]")
        # Always focus the input so typing works immediately
        self.set_focus(self.query_one("#input", Input))

    def _header_text(self) -> str:
        return (
            f"[bold cyan]CALIBER[/] v{__version__}  "
            f"[dim]| Ctrl+P plan/build | Ctrl+C quit | Esc focus input[/]"
        )

    def _status_text(self) -> str:
        cfg = load_config()
        key = "key✓" if get_api_key() else "key✗"
        busy = " [yellow]WORKING…[/]" if self.busy else ""
        return (
            f"mode={cfg.get('mode', 'build')}  "
            f"effort={cfg.get('effort', 'medium')}  "
            f"models={cfg.get('model_mode', 'best')}  "
            f"{key}  tokens={self.agent.total_tokens}{busy}"
        )

    def refresh_status(self) -> None:
        try:
            self.query_one("#status", Static).update(self._status_text())
        except Exception:
            pass

    def action_focus_input(self) -> None:
        self.set_focus(self.query_one("#input", Input))

    @on(Input.Submitted, "#input")
    def on_submit(self, event: Input.Submitted) -> None:
        text = (event.value or "").strip()
        event.input.value = ""
        if not text:
            return
        if self.busy:
            self.query_one("#log", RichLog).write("[yellow]Busy — please wait[/]")
            return

        if text.startswith("/"):
            self.handle_command(text)
            self.set_focus(event.input)
            return

        log = self.query_one("#log", RichLog)
        log.write("")
        log.write(f"[bold green]you[/] [dim]{_ts()}[/]")
        log.write(text)
        self.busy = True
        self.refresh_status()
        self.run_agent(text)

    @work(thread=True, exclusive=True)
    def run_agent(self, text: str) -> None:
        import caliber.agent as agent_mod
        from rich.console import Console

        old = agent_mod.console
        agent_mod.console = Console(quiet=True)
        try:
            result = self.agent.run(text)
            self.call_from_thread(self.show_result, result or "(empty)")
        except Exception as e:
            self.call_from_thread(self.show_error, str(e))
        finally:
            agent_mod.console = old

    def show_result(self, result: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[bold cyan]caliber[/] [dim]{_ts()}[/]")
        for line in result.splitlines() or ["(empty)"]:
            log.write(line)
        log.write("[dim]─────────────────────────────────────[/]")
        self.busy = False
        self.refresh_status()
        self.set_focus(self.query_one("#input", Input))

    def show_error(self, err: str) -> None:
        self.query_one("#log", RichLog).write(f"[red]Error:[/] {err}")
        self.busy = False
        self.refresh_status()
        self.set_focus(self.query_one("#input", Input))

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
                "/provider KEY  /plan  /build  /effort low|medium|high|max|ultra  "
                "/init  /models  /status  /exit"
            )
        elif name == "/provider":
            if rest:
                set_api_key(rest)
                log.write("[green]API key saved.[/]")
            else:
                log.write("Usage: /provider sk-or-...")
        elif name == "/plan":
            cfg["mode"] = "plan"
            save_config(cfg)
            log.write("[cyan]→ plan[/]")
        elif name == "/build":
            cfg["mode"] = "build"
            save_config(cfg)
            log.write("[green]→ build[/]")
        elif name == "/effort":
            if rest in ("low", "medium", "high", "max", "ultra"):
                cfg["effort"] = rest
                save_config(cfg)
                log.write(f"[green]effort → {rest}[/]")
            else:
                log.write("/effort low|medium|high|max|ultra")
        elif name == "/model":
            if rest in ("best", "custom"):
                cfg["model_mode"] = rest
                save_config(cfg)
                log.write(f"models → {rest}")
            else:
                log.write("/model best|custom")
        elif name == "/status":
            log.write(self._status_text())
        elif name == "/init":
            if not get_api_key():
                log.write("[yellow]/provider first[/]")
            else:
                self.busy = True
                self.refresh_status()
                self.run_init()
                return
        elif name == "/models":
            self.busy = True
            self.refresh_status()
            self.run_models()
            return
        else:
            log.write(f"Unknown: {name}  (/help)")
        self.refresh_status()

    @work(thread=True, exclusive=True)
    def run_init(self) -> None:
        try:
            r = self.agent.init_project()
            self.call_from_thread(self.show_result, r)
        except Exception as e:
            self.call_from_thread(self.show_error, str(e))

    @work(thread=True, exclusive=True)
    def run_models(self) -> None:
        from .models import fetch_all_models

        try:
            models = fetch_all_models()
            free = sum(1 for m in models if m.get("note") == "(free)")
            lines = [f"{len(models)} models ({free} free)"] + [
                f"  {m['id']}{(' ' + m['note']) if m.get('note') else ''}" for m in models[:25]
            ]
            self.call_from_thread(self.show_result, "\n".join(lines))
        except Exception as e:
            self.call_from_thread(self.show_error, str(e))

    def action_toggle_mode(self) -> None:
        cfg = load_config()
        cfg["mode"] = "plan" if cfg.get("mode") == "build" else "build"
        save_config(cfg)
        self.query_one("#log", RichLog).write(f"→ {cfg['mode']}")
        self.refresh_status()


def run_tui() -> None:
    CaliberApp().run()
