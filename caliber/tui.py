from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, Markdown, RichLog, Static

from . import __version__
from .agent import CaliberAgent
from .config import get_api_key, load_config, save_config, set_api_key


class StatusBar(Static):
    """Top status strip."""

    def update_status(self, agent: CaliberAgent) -> None:
        cfg = load_config()
        key = "on" if get_api_key() else "off"
        mode = cfg.get("mode", "build")
        effort = cfg.get("effort", "medium")
        models = cfg.get("model_mode", "best")
        tokens = agent.total_tokens
        cwd = Path.cwd().name
        self.update(
            f"  [bold cyan]CALIBER[/]  v{__version__}  │  "
            f"[dim]{cwd}[/]  │  "
            f"mode:[bold]{mode}[/]  effort:[bold]{effort}[/]  models:[bold]{models}[/]  │  "
            f"key:[bold]{key}[/]  tokens:[bold]{tokens}[/]"
        )


class Sidebar(Static):
    """Right sidebar with session info."""

    def compose(self) -> ComposeResult:
        yield Label("[bold]Session[/]", classes="side-title")
        yield Static("", id="side-info")
        yield Label("[bold]Last trace[/]", classes="side-title")
        yield Static("—", id="side-trace")
        yield Label("[bold]Commands[/]", classes="side-title")
        yield Static(
            "[dim]/init[/]  AGENTS.md\n"
            "[dim]/plan[/]  read-only\n"
            "[dim]/build[/] full tools\n"
            "[dim]/model[/] specialists\n"
            "[dim]/effort[/] depth\n"
            "[dim]/provider[/] API key\n"
            "[dim]/status[/] details\n"
            "[dim]/help[/]  commands\n"
            "[dim]Ctrl+C[/]  quit",
            id="side-cmds",
        )

    def refresh_info(self, agent: CaliberAgent) -> None:
        cfg = load_config()
        info = self.query_one("#side-info", Static)
        info.update(
            f"mode   {cfg.get('mode')}\n"
            f"effort {cfg.get('effort')}\n"
            f"models {cfg.get('model_mode')}\n"
            f"tokens {agent.total_tokens}\n"
            f"key    {'set' if get_api_key() else 'missing'}"
        )
        trace = self.query_one("#side-trace", Static)
        if agent.last_trace:
            lines = []
            for s in agent.last_trace[-6:]:
                lines.append(f"{s['task'][:8]:8} {s['tokens']}t")
            trace.update("\n".join(lines))
        else:
            trace.update("—")


class ChatLog(VerticalScroll):
    """Scrollable chat history."""

    def add_user(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M")
        self.mount(Static(f"[bold green]you[/] [dim]{ts}[/]\n{text}", classes="msg user"))
        self.scroll_end(animate=False)

    def add_assistant(self, text: str) -> Markdown:
        ts = datetime.now().strftime("%H:%M")
        header = Static(f"[bold cyan]caliber[/] [dim]{ts}[/]", classes="msg-header")
        body = Markdown(text or "…", classes="msg assistant")
        self.mount(header)
        self.mount(body)
        self.scroll_end(animate=False)
        return body

    def add_system(self, text: str) -> None:
        self.mount(Static(f"[dim]{text}[/]", classes="msg system"))
        self.scroll_end(animate=False)

    def add_tool(self, text: str) -> None:
        self.mount(Static(f"  [dim]→ {text}[/]", classes="msg tool"))
        self.scroll_end(animate=False)


class CaliberApp(App):
    """Full-screen Caliber TUI — OpenCode-inspired layout."""

    CSS = """
    Screen {
        background: #0a0a0b;
        layout: vertical;
    }

    #status {
        dock: top;
        height: 1;
        background: #121216;
        color: #c8c8d0;
        padding: 0 1;
    }

    #main {
        height: 1fr;
        layout: horizontal;
    }

    #chat-panel {
        width: 1fr;
        border: solid #2a2a32;
        background: #0c0c0e;
    }

    #chat {
        height: 1fr;
        padding: 0 1;
    }

    .msg {
        margin: 1 0 0 0;
    }

    .msg.user {
        color: #e8e8ed;
    }

    .msg.system {
        color: #6a6a78;
        margin: 0;
    }

    .msg.tool {
        color: #5a8a6a;
        margin: 0;
    }

    .msg-header {
        margin-top: 1;
        color: #8ab4f8;
    }

    .msg.assistant {
        margin: 0 0 1 0;
        color: #d0d0d8;
    }

    #sidebar {
        width: 28;
        border: solid #2a2a32;
        background: #101014;
        padding: 1;
        overflow-y: auto;
    }

    .side-title {
        color: #8ab4f8;
        margin-top: 1;
        text-style: bold;
    }

    #side-info, #side-trace, #side-cmds {
        color: #a0a0b0;
        margin-bottom: 1;
    }

    #input-row {
        dock: bottom;
        height: 3;
        background: #121216;
        border-top: solid #2a2a32;
        padding: 0 1;
    }

    #prompt {
        width: 1fr;
        background: #0c0c0e;
        border: solid #3a3a48;
        color: #e8e8ed;
    }

    #prompt:focus {
        border: solid #5b8def;
    }

    Footer {
        background: #121216;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "toggle_plan", "Plan/Build"),
        Binding("f1", "show_help", "Help"),
    ]

    TITLE = "Caliber Agent"
    SUB_TITLE = f"v{__version__}"

    busy: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.agent = CaliberAgent()

    def compose(self) -> ComposeResult:
        yield StatusBar(id="status")
        with Horizontal(id="main"):
            with Vertical(id="chat-panel"):
                yield ChatLog(id="chat")
            yield Sidebar(id="sidebar")
        with Horizontal(id="input-row"):
            yield Input(placeholder="Ask Caliber…  (/ for commands)", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#status", StatusBar).update_status(self.agent)
        self.query_one("#sidebar", Sidebar).refresh_info(self.agent)
        chat = self.query_one("#chat", ChatLog)
        chat.add_system(f"Caliber Agent v{__version__} · multi-model coding agent")
        chat.add_system(f"Project: {Path.cwd()}")
        if not get_api_key():
            chat.add_system("[yellow]No API key — type /provider to add your OpenRouter key[/]")
        else:
            chat.add_system("Ready. Type a request or /help")
        self.query_one("#prompt", Input).focus()

    def _refresh_ui(self) -> None:
        self.query_one("#status", StatusBar).update_status(self.agent)
        self.query_one("#sidebar", Sidebar).refresh_info(self.agent)

    @on(Input.Submitted, "#prompt")
    async def on_submit(self, event: Input.Submitted) -> None:
        text = (event.value or "").strip()
        event.input.value = ""
        if not text or self.busy:
            return

        if text.startswith("/"):
            await self._handle_command(text)
            return

        chat = self.query_one("#chat", ChatLog)
        chat.add_user(text)
        self.busy = True
        self.run_agent(text)

    @work(thread=True)
    def run_agent(self, text: str) -> None:
        chat = self.query_one("#chat", ChatLog)
        try:
            # Monkey-patch console tool prints into TUI
            result = self.agent.run(text)
            self.call_from_thread(self._show_result, result)
        except Exception as e:
            self.call_from_thread(chat.add_system, f"[red]Error: {e}[/]")
        finally:
            self.call_from_thread(self._done)

    def _show_result(self, result: str) -> None:
        chat = self.query_one("#chat", ChatLog)
        chat.add_assistant(result or "(empty)")
        self._refresh_ui()

    def _done(self) -> None:
        self.busy = False
        self._refresh_ui()
        self.query_one("#prompt", Input).focus()

    async def _handle_command(self, cmd: str) -> None:
        chat = self.query_one("#chat", ChatLog)
        name = cmd.strip().split(maxsplit=1)[0].lower()
        rest = cmd.strip()[len(name):].strip()
        cfg = load_config()

        if name in ("/exit", "/quit", "/q"):
            self.exit()
            return

        if name == "/help":
            chat.add_system(
                "Commands: /provider /model /models /effort /plan /build /init /status /usage /help /exit\n"
                "Keys: Ctrl+P plan/build · Ctrl+C quit · F1 help"
            )
        elif name == "/provider":
            if rest:
                set_api_key(rest)
                chat.add_system("[green]API key saved.[/]")
            else:
                chat.add_system("Usage: /provider sk-or-...")
        elif name == "/plan":
            cfg["mode"] = "plan"
            save_config(cfg)
            chat.add_system("[cyan]→ Plan mode (read-only)[/]")
        elif name == "/build":
            cfg["mode"] = "build"
            save_config(cfg)
            chat.add_system("[green]→ Build mode (full tools)[/]")
        elif name == "/effort":
            if rest in ("low", "medium", "high", "max", "ultra"):
                cfg["effort"] = rest
                save_config(cfg)
                chat.add_system(f"[green]Effort → {rest}[/]")
            else:
                chat.add_system("Usage: /effort low|medium|high|max|ultra")
        elif name == "/model":
            if rest in ("best", "custom"):
                cfg["model_mode"] = rest
                save_config(cfg)
                chat.add_system(f"[green]Model mode → {rest}[/]")
            else:
                chat.add_system("Usage: /model best|custom  (use terminal /model for full picker)")
        elif name == "/status":
            self._refresh_ui()
            chat.add_system(
                f"mode={cfg.get('mode')} effort={cfg.get('effort')} "
                f"models={cfg.get('model_mode')} tokens={self.agent.total_tokens}"
            )
        elif name == "/usage":
            chat.add_system(f"Session tokens: {self.agent.total_tokens}")
        elif name == "/init":
            if not get_api_key():
                chat.add_system("[yellow]Set /provider first[/]")
            else:
                self.busy = True
                self._run_init()
                return
        elif name == "/models":
            chat.add_system("Fetching catalog…")
            self._run_models()
            return
        else:
            chat.add_system(f"Unknown command: {name}  (/help)")

        self._refresh_ui()

    @work(thread=True)
    def _run_init(self) -> None:
        chat = self.query_one("#chat", ChatLog)
        try:
            result = self.agent.init_project()
            self.call_from_thread(chat.add_assistant, result)
        except Exception as e:
            self.call_from_thread(chat.add_system, f"[red]{e}[/]")
        finally:
            self.call_from_thread(self._done)

    @work(thread=True)
    def _run_models(self) -> None:
        from .models import fetch_all_models
        chat = self.query_one("#chat", ChatLog)
        try:
            models = fetch_all_models()
            free = sum(1 for m in models if m.get("note") == "(free)")
            sample = "\n".join(f"  {m['id']}" for m in models[:12])
            self.call_from_thread(
                chat.add_system,
                f"{len(models)} models ({free} free). Sample:\n{sample}\n…",
            )
        except Exception as e:
            self.call_from_thread(chat.add_system, f"[red]{e}[/]")
        self.call_from_thread(self._refresh_ui)

    def action_toggle_plan(self) -> None:
        cfg = load_config()
        cfg["mode"] = "plan" if cfg.get("mode") == "build" else "build"
        save_config(cfg)
        chat = self.query_one("#chat", ChatLog)
        chat.add_system(f"→ {cfg['mode']} mode")
        self._refresh_ui()

    def action_show_help(self) -> None:
        chat = self.query_one("#chat", ChatLog)
        chat.add_system(
            "/provider /model /effort /plan /build /init /models /status /help /exit · Ctrl+P toggle mode"
        )


def run_tui() -> None:
    app = CaliberApp()
    app.run()
