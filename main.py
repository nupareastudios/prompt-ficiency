#!/usr/bin/env python3
"""
Code-Assist Usage Evaluator
────────────────────────────
Evaluates how effectively users are leveraging AI coding tools
(GitHub Copilot, Claude Code, Cursor, etc.) by analysing their
prompt logs using a LangChain Deep Agent backed by Azure OpenAI.

Usage:
    python main.py evaluate path/to/agent.log
    python main.py evaluate session.pdf --verbose
"""

import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()

SUPPORTED_EXTENSIONS = [".log", ".txt", ".doc", ".docx", ".pdf"]

RATING_COLORS = {
    (0, 3): "bold red",
    (3, 6): "bold yellow",
    (6, 8): "bold cyan",
    (8, 10): "bold green",
}


def rating_color(score: float) -> str:
    for (lo, hi), color in RATING_COLORS.items():
        if lo <= score < hi:
            return color
    return "bold green"


def rating_label(score: float) -> str:
    if score < 3:
        return "Needs Significant Improvement"
    if score < 6:
        return "Below Average"
    if score < 8:
        return "Good"
    return "Excellent"


def draw_rating_bar(score: float, width: int = 40) -> Text:
    filled = int(round((score / 10) * width))
    bar = "█" * filled + "░" * (width - filled)
    color = rating_color(score)
    t = Text()
    t.append(bar, style=color)
    return t


def print_header():
    console.print()
    console.print(
        Panel.fit(
            "[bold white]Code-Assist Usage Evaluator[/bold white]\n"
            "[dim]Powered by LangChain Deep Agents + Azure OpenAI[/dim]",
            border_style="bright_blue",
            padding=(1, 4),
        )
    )
    console.print()


def print_result(result: dict, file_path: str, verbose: bool):
    rating = result.get("rating")
    summary = result.get("summary", "")
    strengths = result.get("strengths", [])
    weaknesses = result.get("weaknesses", [])
    tips = result.get("improvement_tips", [])
    benchmark = result.get("industry_benchmark", "")

    console.print(Rule("[bold bright_blue]Evaluation Report[/bold bright_blue]"))
    console.print(f"[dim]File:[/dim] [bold]{escape(file_path)}[/bold]\n")

    # ── Rating ────────────────────────────────────────────────────────────────
    if rating is not None:
        score = float(rating)
        color = rating_color(score)
        label = rating_label(score)

        score_text = Text(f"  {score:.1f} / 10  ", style=f"bold white on {color.split()[-1]}")
        console.print(Text("  Rating: ") + score_text + Text(f"  {label}", style=color))
        console.print()
        console.print(Text("  ") + draw_rating_bar(score))
        console.print()
    else:
        console.print("[yellow]  Rating could not be determined.[/yellow]\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print(
        Panel(
            escape(summary),
            title="[bold]Summary[/bold]",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )
    console.print()

    # ── Strengths & Weaknesses ────────────────────────────────────────────────
    sw_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    sw_table.add_column("✅  Strengths", style="green", ratio=1)
    sw_table.add_column("⚠️  Weaknesses", style="red", ratio=1)

    max_rows = max(len(strengths), len(weaknesses))
    for i in range(max_rows):
        s = strengths[i] if i < len(strengths) else ""
        w = weaknesses[i] if i < len(weaknesses) else ""
        sw_table.add_row(escape(s), escape(w))

    console.print(sw_table)
    console.print()

    # ── Improvement Tips ──────────────────────────────────────────────────────
    if tips:
        console.print(Rule("[bold]Improvement Tips[/bold]"))
        for idx, tip in enumerate(tips, 1):
            tip_text = tip.get("tip", "")
            before = tip.get("example_before", "")
            after = tip.get("example_after", "")

            console.print(f"\n  [bold cyan]{idx}.[/bold cyan] {escape(tip_text)}")
            if verbose and before:
                console.print(
                    Panel(
                        f"[red]Before:[/red]\n{escape(before)}\n\n[green]After:[/green]\n{escape(after)}",
                        border_style="dim",
                        padding=(0, 2),
                    )
                )
        console.print()

    # ── Industry Benchmark ────────────────────────────────────────────────────
    if benchmark:
        console.print(
            Panel(
                escape(benchmark),
                title="[bold]Industry Benchmark[/bold]",
                border_style="yellow",
                padding=(0, 2),
            )
        )
        console.print()


# ─── CLI ─────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Code-Assist Usage Evaluator — analyse AI coding tool logs."""


@cli.command()
@click.argument("log_file", type=click.Path(exists=True))
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Show before/after prompt examples for each improvement tip.",
)
@click.option(
    "--output", "-o",
    type=click.Choice(["pretty", "json"], case_sensitive=False),
    default="pretty",
    show_default=True,
    help="Output format.",
)
def evaluate(log_file: str, verbose: bool, output: str):
    """Evaluate an AI coding-assistant log file.

    LOG_FILE can be a .log, .txt, .doc, .docx, or .pdf file.
    """
    path = Path(log_file)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        console.print(
            f"[bold red]Error:[/bold red] Unsupported file type '{path.suffix}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
        sys.exit(1)

    print_header()

    # Read the log file
    try:
        from evaluator.parsers import read_log_file
        raw_text = read_log_file(log_file)
    except Exception as exc:
        console.print(f"[bold red]Failed to read file:[/bold red] {escape(str(exc))}")
        sys.exit(1)

    if not raw_text.strip():
        console.print("[bold red]Error:[/bold red] The file appears to be empty.")
        sys.exit(1)

    char_count = len(raw_text)
    console.print(
        f"[dim]Loaded [bold]{path.name}[/bold] "
        f"({char_count:,} characters)[/dim]\n"
    )

    # Run the agent
    with Progress(
        SpinnerColumn(spinner_name="dots", style="bright_blue"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("Analysing prompts with Deep Agent…", total=None)
        try:
            from evaluator.agent import evaluate_log
            result = evaluate_log(raw_text)
        except EnvironmentError as exc:
            console.print(f"\n[bold red]Configuration Error:[/bold red]\n{escape(str(exc))}")
            sys.exit(1)
        except Exception as exc:
            console.print(f"\n[bold red]Agent Error:[/bold red] {escape(str(exc))}")
            sys.exit(1)

    if output == "json":
        import json
        console.print_json(json.dumps(result, indent=2))
    else:
        print_result(result, log_file, verbose)


@cli.command()
def config():
    """Show current Azure OpenAI configuration status."""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    print_header()
    console.print(Rule("[bold]Azure OpenAI Configuration[/bold]"))
    console.print()

    keys = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_API_VERSION",
    ]

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Variable", style="cyan")
    table.add_column("Status")
    table.add_column("Value (masked)")

    for key in keys:
        val = os.getenv(key, "")
        if val:
            masked = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
            table.add_row(key, "[green]✓ Set[/green]", masked)
        else:
            table.add_row(key, "[red]✗ Missing[/red]", "[dim]—[/dim]")

    console.print(table)
    console.print(
        "\n[dim]Copy [bold].env.example[/bold] to [bold].env[/bold] "
        "and fill in your credentials.[/dim]\n"
    )


if __name__ == "__main__":
    cli()
