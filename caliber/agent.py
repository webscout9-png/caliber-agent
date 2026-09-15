from __future__ import annotations

from typing import Any, Dict, List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import load_config
from .openrouter import chat
from .router import classify_task, decompose, get_model_for_task

console = Console()

class CaliberAgent:
    """Specialized multi-model orchestrator."""

    def __init__(self) -> None:
        self.cfg = load_config()
        self.total_tokens = 0
        self.last_trace: List[Dict[str, Any]] = []

    def reload(self) -> None:
        self.cfg = load_config()

    def run(self, user_input: str) -> str:
        self.reload()
        self.last_trace = []
        effort = self.cfg.get("effort", "medium")
        mode = self.cfg.get("mode", "build")

        if mode == "plan":
            return self._plan_only(user_input)

        return self._build(user_input, effort)

    def _plan_only(self, user_input: str) -> str:
        model = get_model_for_task("planning")
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Caliber Agent in pure PLAN mode. "
                    "Produce a clear, actionable, high-quality plan. "
                    "Do not implement anything. Focus on structure, risks, and steps."
                ),
            },
            {"role": "user", "content": user_input},
        ]
        with Progress(SpinnerColumn(), TextColumn("[bold blue]Planning..."), transient=True) as progress:
            progress.add_task("plan", total=None)
            result = chat(model, messages, temperature=0.3)
        self._track(result, "planning", model)
        return result["content"]

    def _build(self, user_input: str, effort: str) -> str:
        steps = decompose(user_input, effort)
        context_pieces: List[str] = []
        outputs: List[str] = []

        for i, step in enumerate(steps, 1):
            task_type = step["type"]
            instruction = step["instruction"]
            model = get_model_for_task(task_type)

            system = (
                f"You are a specialist inside Caliber Agent.\n"
                f"Your specialist role: {task_type.upper()}\n"
                f"Effort level: {effort}\n"
                f"Be precise, high-signal, and complete for your role. "
                f"Do not add fluff. Focus only on what this specialist should produce."
            )

            messages: List[Dict[str, str]] = [{"role": "system", "content": system}]

            if context_pieces:
                # Give limited recent context so specialists stay focused
                recent = "\n\n---\n\n".join(context_pieces[-3:])
                messages.append({
                    "role": "user",
                    "content": f"Context from previous specialist steps:\n\n{recent}",
                })

            messages.append({"role": "user", "content": instruction})

            label = f"Step {i}/{len(steps)} · {task_type} · {model}"
            with Progress(SpinnerColumn(), TextColumn(f"[bold cyan]{label}"), transient=True) as progress:
                progress.add_task("step", total=None)
                result = chat(model, messages, temperature=0.35)

            self._track(result, task_type, model)
            content = result["content"]
            context_pieces.append(f"[{task_type.upper()}]\n{content}")
            outputs.append(content)

        # Final synthesis when we had multiple specialist steps
        if len(outputs) > 1:
            return self._synthesize(user_input, outputs, effort)

        return outputs[0] if outputs else "No output generated."

    def _synthesize(self, original_request: str, outputs: List[str], effort: str) -> str:
        model = get_model_for_task("writing")
        combined = "\n\n=====\n\n".join(outputs)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the final synthesizer of Caliber Agent. "
                    "Take all specialist outputs and produce one clean, coherent, "
                    "complete answer for the user. Preserve important details and code. "
                    "Remove redundancy. Structure the answer well."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original user request:\n{original_request}\n\n"
                    f"Specialist outputs:\n{combined}\n\n"
                    "Produce the final answer now."
                ),
            },
        ]

        with Progress(SpinnerColumn(), TextColumn("[bold green]Synthesizing final answer..."), transient=True) as progress:
            progress.add_task("synth", total=None)
            result = chat(model, messages, temperature=0.3)

        self._track(result, "writing", model)
        return result["content"]

    def _track(self, result: Dict[str, Any], task_type: str, model: str) -> None:
        usage = result.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        self.total_tokens += tokens
        self.last_trace.append({
            "task": task_type,
            "model": model,
            "tokens": tokens,
        })
