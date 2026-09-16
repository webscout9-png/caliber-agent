from __future__ import annotations

import typer

from . import __version__

app = typer.Typer(
    add_completion=False,
    help="Caliber Agent — multi-model coding agent with full TUI",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    classic: bool = typer.Option(False, "--classic", help="Use classic prompt UI instead of full TUI"),
) -> None:
    """Launch Caliber (full-screen TUI by default)."""
    if ctx.invoked_subcommand is not None:
        return

    if classic:
        from .classic import run_classic

        run_classic()
        return

    try:
        from .tui import run_tui

        run_tui()
    except ImportError:
        print("Textual not installed — falling back to classic UI.")
        print("Install full TUI:  pip install 'textual>=0.80'")
        from .classic import run_classic

        run_classic()


if __name__ == "__main__":
    app()
