from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import load_config
from .openrouter import chat, chat_with_tools
from .router import classify_task, get_model_for_task
from .tools import (
    TOOL_SPECS,
    execute_tool,
    get_cwd,
    set_cwd,
    tool_list_dir,
    tool_write_file,
)

console = Console()

SYSTEM_BUILD = """You are Caliber Agent in BUILD mode — a powerful coding agent.

You have tools: list_dir, glob, read_file, write_file, edit, grep, bash, webfetch.

Rules:
- Explore with glob/grep/read before editing.
- Prefer `edit` for precise changes; use `write_file` for new files.
- Use bash for tests, installs, git — not for reading/writing files.
- Be minimal and correct. Do not over-engineer.
- When done, give a clear summary of what changed.

Specialist focus: {focus}
Effort: {effort}

{project_ctx}
"""

SYSTEM_PLAN = """You are Caliber Agent in PLAN mode — read-only analysis.

You can use: list_dir, glob, read_file, grep, webfetch.
You CANNOT write files, edit, or run bash.

Produce a clear plan: steps, files involved, risks, success criteria.
Do not implement.

{project_ctx}
"""

class CaliberAgent:
    def __init__(self) -> None:
        self.cfg = load_config()
        self.total_tokens = 0
        self.last_trace: List[Dict[str, Any]] = []
        set_cwd(Path.cwd())

    def reload(self) -> None:
        self.cfg = load_config()

    def run(self, user_input: str) -> str:
        self.reload()
        self.last_trace = []
        effort = self.cfg.get("effort", "medium")
        mode = self.cfg.get("mode", "build")
        project_ctx = self._project_context()

        if mode == "plan":
            return self._agent_loop(
                user_input,
                effort,
                project_ctx,
                allow_write=False,
                allow_bash=False,
                system_template=SYSTEM_PLAN,
            )

        plan_note = ""
        if effort in ("high", "max", "ultra"):
            try:
                plan_note = self._specialist_plan(user_input, project_ctx)
            except Exception as e:
                console.print(f"[yellow]Planning specialist skipped: {e}[/]")

        return self._agent_loop(
            user_input,
            effort,
            project_ctx,
            allow_write=True,
            allow_bash=True,
            system_template=SYSTEM_BUILD,
            extra_context=plan_note,
        )

    def _project_context(self) -> str:
        parts = [f"Project root: {get_cwd()}"]
        for name in ("AGENTS.md", "CLAUDE.md"):
            p = get_cwd() / name
            if p.exists():
                try:
                    parts.append(f"{name}:\n" + p.read_text(encoding="utf-8")[:4000])
                    break
                except Exception:
                    pass
        else:
            try:
                parts.append("Top-level:\n" + tool_list_dir(".")[:1200])
            except Exception:
                pass
        return "\n\n".join(parts)

    def _specialist_plan(self, user_input: str, project_ctx: str) -> str:
        model = get_model_for_task("planning")
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Planning specialist. Create a precise implementation plan.\n"
                    "List concrete files and steps. No fluff.\n\n" + project_ctx
                ),
            },
            {"role": "user", "content": user_input},
        ]
        with Progress(SpinnerColumn(), TextColumn(f"[bold blue]Plan specialist · {model}"), transient=True) as progress:
            progress.add_task("p", total=None)
            res = chat(model, messages, temperature=0.25)
        self._track(res, "planning", model)
        return "\nApproved plan from planning specialist:\n" + res["content"]

    def _agent_loop(
        self,
        user_input: str,
        effort: str,
        project_ctx: str,
        allow_write: bool,
        allow_bash: bool,
        system_template: str,
        extra_context: str = "",
    ) -> str:
        focus = classify_task(user_input)
        model = get_model_for_task("coding" if focus == "coding" else focus)

        system = system_template.format(focus=focus, effort=effort, project_ctx=project_ctx)
        if extra_context:
            system += "\n" + extra_context

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_input},
        ]

        max_rounds = {"low": 5, "medium": 10, "high": 14, "max": 18, "ultra": 24}.get(effort, 10)
        final_content = ""

        for round_i in range(max_rounds):
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[bold cyan]Loop {round_i+1}/{max_rounds} · {model}"),
                transient=True,
            ) as progress:
                progress.add_task("l", total=None)
                try:
                    result = chat_with_tools(model, messages, TOOL_SPECS, temperature=0.25)
                except Exception as e:
                    console.print(f"[red]Model error: {e}[/]")
                    # last resort: plain chat without tools
                    try:
                        result = chat(model, [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user_input},
                        ])
                        self._track(result, focus, model)
                        return result["content"] or str(e)
                    except Exception as e2:
                        return f"Failed to complete request: {e2}"

            self._track(result, focus, model)
            tool_calls = result.get("tool_calls") or []
            content = result.get("content") or ""
            final_content = content or final_content

            if not tool_calls:
                break

            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except Exception:
                    args = {}
                short = json.dumps(args)[:90]
                console.print(f"  [dim]→ {name}({short})[/]")
                try:
                    out = execute_tool(name, args, allow_write=allow_write, allow_bash=allow_bash)
                except Exception as te:
                    out = f"Tool error: {te}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", "call"),
                    "content": out[:14000],
                })

        if effort in ("max", "ultra") and final_content and allow_write:
            try:
                return self._critique(user_input, final_content)
            except Exception as e:
                console.print(f"[yellow]Critique skipped: {e}[/]")

        return final_content or "Done."

    def _critique(self, original: str, draft: str) -> str:
        model = get_model_for_task("critique")
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Critique specialist. Review the work. "
                    "Fix errors, tighten the answer, return the final polished response."
                ),
            },
            {
                "role": "user",
                "content": f"Request:\n{original}\n\nDraft:\n{draft}\n\nFinal answer:",
            },
        ]
        with Progress(SpinnerColumn(), TextColumn(f"[bold magenta]Critique · {model}"), transient=True) as progress:
            progress.add_task("c", total=None)
            res = chat(model, messages, temperature=0.2)
        self._track(res, "critique", model)
        return res["content"]

    def init_project(self) -> str:
        """/init — create AGENTS.md like OpenCode."""
        model = get_model_for_task("planning")
        tree = tool_list_dir(".")
        samples = []
        for candidate in ["README.md", "package.json", "pyproject.toml", "Cargo.toml", "go.mod"]:
            p = get_cwd() / candidate
            if p.exists():
                try:
                    samples.append(f"### {candidate}\n" + p.read_text(encoding="utf-8")[:1500])
                except Exception:
                    pass

        messages = [
            {
                "role": "system",
                "content": (
                    "Analyze this project and write a concise AGENTS.md for an AI coding agent.\n"
                    "Include: project purpose, structure, key commands, conventions, and gotchas.\n"
                    "Be short and actionable. Output ONLY the markdown content."
                ),
            },
            {
                "role": "user",
                "content": f"Root listing:\n{tree}\n\n" + "\n\n".join(samples),
            },
        ]
        with Progress(SpinnerColumn(), TextColumn("[bold blue]Generating AGENTS.md..."), transient=True) as progress:
            progress.add_task("i", total=None)
            res = chat(model, messages, temperature=0.3)
        self._track(res, "planning", model)
        content = res["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        path = get_cwd() / "AGENTS.md"
        tool_write_file("AGENTS.md", content.strip() + "\n")
        return f"Created {path}\n\n" + content[:2000]

    def _track(self, result: Dict[str, Any], task_type: str, model: str) -> None:
        usage = result.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        self.total_tokens += tokens
        self.last_trace.append({"task": task_type, "model": model, "tokens": tokens})
