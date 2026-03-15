from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from llmbench.backends import BackendConnectionError
from llmbench.config import ConfigError, load_run_config
from llmbench.runner import BenchmarkRunner, check_backend

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def check(config_path: Path) -> None:
    """Check vLLM is reachable and configured model is listed."""
    try:
        config = load_run_config(config_path)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    try:
        asyncio.run(check_backend(config))
    except BackendConnectionError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("vLLM connectivity check passed", fg=typer.colors.GREEN)


@app.command()
def run(config_path: Path) -> None:
    """Run benchmark; write CSV, plots, summary to run dir."""
    try:
        config = load_run_config(config_path)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    runner = BenchmarkRunner()
    try:
        run_dir = runner.run(config)
    except BackendConnectionError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("Benchmark complete", fg=typer.colors.GREEN)
    typer.echo(f"Run directory: {run_dir}")
    typer.echo(f"Summary report: {run_dir / 'summary.md'}")


if __name__ == "__main__":
    app()
