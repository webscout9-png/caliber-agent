from __future__ import annotations

import typer

app = typer.Typer(
    add_completion=False,
    help="Caliber Agent — multi-model coding agent",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    classic: bool = typer.Option(False, "--classic", help="Classic prompt UI"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    if classic:
        from .classic import run_classic

        run_classic()
        return

    try:
        import textual  # noqa: F401
        from .tui import run_tui

        run_tui()
    except ImportError:
        print("Installing textual is recommended for the full UI:")
        print("  pip install 'textual>=0.80'")
        print("Starting classic UI…\n")
        from .classic import run_classic

        run_classic()
    except Exception as e:
        print(f"TUI failed ({e}). Starting classic UI…\n")
        from .classic import run_classic

        run_classic()


if __name__ == "__main__":
    app()
