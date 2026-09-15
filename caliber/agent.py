from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import load_config, save_config
from .openrouter import chat
from .router import classify_task, decompose, get_model_for_task

console = Console()

class CaliberAgent:
    def __init__(self) -> None:
        self.cfg = load_config()
        self.total_tokens = 0
        self.session_messages: List[Dict[str, str]] = []

    def reload(self) -> None:
        self.cfg = load_config()

    def run(self, user_input: str) -> str:
        self.reload()
        effort = self.cfg.get("effort", "medium")
        mode = self.cfg.get("mode", "build")

        if mode == "plan":
            # Plan mode: only produce a plan, do not execute heavy steps
            model = get_model_for_task("planning")
            messages = [
                {"role": "system", "content": "You are Caliber Agent in PLAN mode. Produce a clear, actionable plan. Do not implement."},
                {"role": "user", "content": user_input},
            ]
            with Progress(SpinnerColumn(), TextColumn("[bold blue]Planning..."), transient=True) as progress:
                progress.add_task("plan", total=None)
                result = chat(model, messages)
            self._track(result)
            return result["content"]

        # Build mode: decompose + route
        steps = decompose(user_input, effort)
        context: List[str] = []
        final_parts: List[str] = []

        for i, step in enumerate(steps, 1):
            task_type = step["type"]
            instruction = step["instruction"]
            model = get_model_for_task(task_type)

            system = (
                f"You are Caliber Agent. Current sub-task type: {task_type}. "
                f"Effort level: {effort}. Be precise and high-quality."
            )
            messages = [{"role": "system", "content": system}]
            if context:
                messages.append({"role": "user", "content": "Previous context:\n" + "\n---\n".join(context[-3:])})
            messages.append({"role": "user", "content": instruction})

            with Progress(
                SpinnerColumn(),
                TextColumn(f"[bold cyan]Step {i}/{len(steps)} · {task_type} · {model}"),
                transient=True,
            ) as progress:
                progress.add_task("step", total=None)
                result = chat(model, messages)

            self._track(result)
            content = result["content"]
            context.append(f"[{task_type}]\n{content}")
            final_parts.append(content)

        # Final synthesis if multiple steps
        if len(final_parts) > 1:
            synth_model = get_model_for_task("writing")
            synth_messages = [
                {"role": "system", "content": "Synthesize the following step outputs into one clean, coherent final answer for the user."},
                {"role": "user", "content": "\n\n".join(final_parts)},
            ]
            with Progress(SpinnerColumn(), TextColumn("[bold green]Synthesizing final answer..."), transient=True) as progress:
                progress.add_task("synth", total=None)
                final = chat(synth_model, synth_messages)
            self._track(final)
            return final["content"]

        return final_parts[0] if final_parts else "No output generated."

    def _track(self, result: Dict[str, Any]) -> None:
        usage = result.get("usage", {})
        self.total_tokens += usage.get("total_tokens", 0)
