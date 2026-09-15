from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import load_config
from .openrouter import chat, chat_with_tools
from .router import classify_task, decompose, get_model_for_task
from .tools import TOOL_SPECS, execute_tool, get_cwd, set_cwd, tool_list_dir, tool_read_file

console = Console()

class CaliberAgent:
    """Top-class multi-model coding agent with specialist routing + tool loop."""

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

        # Project context
        project_ctx = self._project_context()

        if mode == "plan":
            return self._plan_only(user_input, project_ctx)

        return self._build_with_tools(user_input, effort, project_ctx)

    def _project_context(self) -> str:
        """Lightweight project awareness (inspired by OpenCode AGENTS.md)."""
        parts = [f"Project root: {get_cwd()}"]
        agents_md = get_cwd() / "AGENTS.md"
        if agents_md.exists():
            try:
                parts.append("AGENTS.md:\n" + agents_md.read_text(encoding="utf-8")[:3000])
            except Exception:
                pass
        else:
            # quick tree snapshot
            try:
                tree = tool_list_dir(".")
                parts.append("Top-level files:\n" + tree[:1500])
            except Exception:
                pass
        return "\n\n".join(parts)

    def _plan_only(self, user_input: str, project_ctx: str) -> str:
        model = get_model_for_task("planning")
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Caliber Agent in PLAN mode (read-only).\n"
                    "Produce a clear, actionable plan. Do NOT edit files or run commands.\n"
                    "Focus on architecture, steps, risks, and success criteria.\n\n"
                    f"{project_ctx}"
                ),
            },
            {"role": "user", "content": user_input},
        ]
        with Progress(SpinnerColumn(), TextColumn("[bold blue]Planning..."), transient=True) as progress:
            progress.add_task("plan", total=None)
            result = chat(model, messages, temperature=0.3)
        self._track(result, "planning", model)
        return result["content"]

    def _build_with_tools(self, user_input: str, effort: str, project_ctx: str) -> str:
        """Full agent loop with tools + multi-model specialists."""
        primary_task = classify_task(user_input)
        allow_bash = True  # build mode

        # High effort: first get a specialist plan
        plan_text = ""
        if effort in ("high", "max", "ultra"):
            plan_model = get_model_for_task("planning")
            plan_msgs = [
                {
                    "role": "system",
                    "content": (
                        "You are the Planning specialist of Caliber Agent.\n"
                        "Create a precise step-by-step plan. Be concrete about files and commands.\n\n"
                        f"{project_ctx}"
                    ),
                },
                {"role": "user", "content": user_input},
            ]
            with Progress(SpinnerColumn(), TextColumn(f"[bold blue]Planning · {plan_model}"), transient=True) as progress:
                progress.add_task("plan", total=None)
                plan_res = chat(plan_model, plan_msgs, temperature=0.25)
            self._track(plan_res, "planning", plan_model)
            plan_text = plan_res["content"]

        # Main execution model (coding specialist for code tasks, else default)
        exec_model = get_model_for_task("coding" if primary_task == "coding" else primary_task)

        system = (
            "You are Caliber Agent — a powerful coding agent with tools.\n"
            f"Current specialist focus: {primary_task}\n"
            f"Effort: {effort}\n"
            "You can call tools to explore and modify the project.\n"
            "Use tools when needed. Prefer minimal, correct changes.\n"
            "When finished, give a clear final answer to the user.\n\n"
            f"{project_ctx}\n"
        )
        if plan_text:
            system += f"\nApproved plan:\n{plan_text}\n"

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_input},
        ]

        max_rounds = {"low": 4, "medium": 8, "high": 12, "max": 16, "ultra": 20}.get(effort, 8)

        for round_i in range(max_rounds):
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[bold cyan]Agent loop {round_i+1}/{max_rounds} · {exec_model}"),
                transient=True,
            ) as progress:
                progress.add_task("loop", total=None)
                result = chat_with_tools(exec_model, messages, TOOL_SPECS, temperature=0.3)

            self._track(result, primary_task, exec_model)

            # Tool calls?
            tool_calls = result.get("tool_calls") or []
            content = result.get("content") or ""

            if not tool_calls:
                # Final answer
                if effort in ("max", "ultra") and content:
                    # Optional critique pass
                    return self._critique_and_polish(user_input, content, effort)
                return content or "Done."

            # Execute tools and feed results back
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
                console.print(f"  [dim]→ tool {name}({json.dumps(args)[:80]})[/]")
                out = execute_tool(name, args, allow_bash=allow_bash)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", "call"),
                    "content": out[:12000],
                })

        return content or "Reached max agent rounds. Partial work may be complete."

    def _critique_and_polish(self, original: str, draft: str, effort: str) -> str:
        model = get_model_for_task("critique")
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Critique specialist. Review the draft answer/work. "
                    "Fix any errors, improve clarity, and return the final polished response."
                ),
            },
            {
                "role": "user",
                "content": f"Original request:\n{original}\n\nDraft:\n{draft}\n\nReturn the improved final answer.",
            },
        ]
        with Progress(SpinnerColumn(), TextColumn(f"[bold magenta]Critique · {model}"), transient=True) as progress:
            progress.add_task("crit", total=None)
            result = chat(model, messages, temperature=0.25)
        self._track(result, "critique", model)
        return result["content"]

    def _track(self, result: Dict[str, Any], task_type: str, model: str) -> None:
        usage = result.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        self.total_tokens += tokens
        self.last_trace.append({"task": task_type, "model": model, "tokens": tokens})
