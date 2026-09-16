from __future__ import annotations

import typer

from . import __version__

app = typer.Typer(
    add_completion=False,
    help="Caliber Agent — multi-model coding agent with full TUI",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Launch the Caliber full-screen TUI."""
    if ctx.invoked_subcommand is not None:
        return
    from .tui import run_tui

    run_tui()


if __name__ == "__main__":
    app()
