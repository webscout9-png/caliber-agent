from __future__ import annotations

import typer

app = typer.Typer(
    add_completion=False,
    help="Caliber Agent",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    tui: bool = typer.Option(False, "--tui", help="Full-screen Textual TUI"),
    classic: bool = typer.Option(False, "--classic", help="Classic prompt UI"),
) -> None:
    """Launch Caliber. Default = classic (always works). Use --tui for full-screen UI."""
    if ctx.invoked_subcommand is not None:
        return

    # Default to classic — reliable prompt you can always type into
    if tui and not classic:
        try:
            from .tui import run_tui

            run_tui()
            return
        except Exception as e:
            print(f"TUI error: {e}\nFalling back to classic UI…\n")

    from .classic import run_classic

    run_classic()


if __name__ == "__main__":
    app()
