import sys
import json
import os
import time
import threading
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, BarColumn,
    TextColumn, TimeElapsedColumn, TaskProgressColumn
)
from rich.live import Live
from rich.layout import Layout
from rich.rule import Rule
from rich.align import Align
from rich.padding import Padding
from rich import box

console = Console()

# ── Brand identity ─────────────────────────────────────────────────────────────

TAGLINE = "Ethical Hacking · AI Patch Engine · v0.1"

# Original ASCII banner — rows ordered top to bottom
_BANNER_ROWS = [
    "  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗      ",
    "  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║      ",
    "  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║      ",
    "  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║      ",
    "  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗  ",
    "  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝  ",
]

# Gradient: deep blue → cyan, one color per row
_GRADIENT = [
    "#1560bd",  # deep blue
    "#1a80d0",
    "#0ea5e9",  # sky blue
    "#06c0d8",
    "#00d4d4",  # cyan-teal
    "#00e5c8",  # bright cyan
]

SEVERITY_COLORS = {
    "High":          "bold red",
    "Medium":        "bold yellow",
    "Low":           "bold cyan",
    "Informational": "dim white",
}

SEVERITY_ICONS = {
    "High":          "●",
    "Medium":        "●",
    "Low":           "●",
    "Informational": "○",
}

SEVERITY_DOT_COLORS = {
    "High":          "red",
    "Medium":        "yellow",
    "Low":           "cyan",
    "Informational": "white",
}


# ── Banner ─────────────────────────────────────────────────────────────────────

def show_banner():
    console.print()
    for row, color in zip(_BANNER_ROWS, _GRADIENT):
        console.print(f"[bold {color}]{row}[/bold {color}]")
    console.print()
    console.print(Align.center(Text(TAGLINE, style="dim white")))
    console.print()
    console.print(Rule(style="dim white"))
    console.print()


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_arg(flag):
    try:
        idx = sys.argv.index(flag)
        return sys.argv[idx + 1]
    except (ValueError, IndexError):
        return None


def _dim_rule(label=""):
    if label:
        console.print(Rule(f"[dim]{label}[/dim]", style="dim white"))
    else:
        console.print(Rule(style="dim white"))


# ── Ethics gate ────────────────────────────────────────────────────────────────

def ethics_check(url):
    console.print()
    console.print(
        Panel(
            Text.assemble(
                ("  Target\n", "bold white"),
                (f"  {url}\n\n", "cyan"),
                ("  You confirm that you:\n", "dim white"),
                ("  • own this target, or\n", "dim white"),
                ("  • hold explicit written permission to test it.\n\n", "dim white"),
                ("  Unauthorized scanning is illegal.", "dim red"),
            ),
            border_style="dim white",
            title="[dim]Authorization Required[/dim]",
            title_align="left",
            padding=(0, 1),
            width=62,
        )
    )
    console.print()
    confirm = console.input("  Type [bold green]YES[/bold green] to confirm → ")
    if confirm.strip().upper() != "YES":
        console.print()
        console.print("  [red]✗[/red] Scan cancelled.\n")
        sys.exit(0)
    console.print()


def validate_url(url):
    if not url.startswith("http"):
        console.print("  [red]✗[/red] URL must start with [cyan]http://[/cyan] or [cyan]https://[/cyan]")
        sys.exit(1)


# ── Live scan UI ───────────────────────────────────────────────────────────────

def run_scan_with_ui(url):
    from src.attack.zap_scanner import run_zap_scan_live

    findings_so_far = []

    _dim_rule("Attack Engine")
    console.print()

    with Progress(
        SpinnerColumn(spinner_name="dots", style="cyan"),
        TextColumn("[bold white]{task.description:<16}"),
        BarColumn(
            bar_width=28,
            style="dim white",
            complete_style="cyan",
            finished_style="green",
        ),
        TaskProgressColumn(style="dim white"),
        TextColumn("[dim]{task.fields[status]}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
        refresh_per_second=12,
    ) as progress:

        spider_task = progress.add_task("Spider", total=100, status="starting…")
        passive_task = progress.add_task("Passive scan", total=100, status="pending")
        active_task = progress.add_task("Active scan", total=100, status="pending")

        def on_spider_progress(pct):
            progress.update(spider_task, completed=pct, status=f"{pct}%")

        def on_spider_done(url_count):
            progress.update(spider_task, completed=100, status=f"[green]✓[/green] {url_count} URLs")

        def on_passive_done():
            progress.update(passive_task, completed=100, status="[green]✓[/green] done")

        def on_active_progress(pct):
            progress.update(active_task, completed=pct, status=f"{pct}%")

        def on_active_done():
            progress.update(active_task, completed=100, status="[green]✓[/green] done")

        def on_finding(finding):
            findings_so_far.append(finding)
            severity = finding["severity"]
            dot_color = SEVERITY_DOT_COLORS.get(severity, "white")
            progress.console.print(
                f"    [{dot_color}]{SEVERITY_ICONS[severity]}[/{dot_color}]"
                f"  [bold white]{finding['vuln_type']}[/bold white]"
                f"  [dim]{finding['endpoint'][:50]}[/dim]"
                f"  [dim]{severity}[/dim]"
            )

        results = run_zap_scan_live(
            url,
            on_spider_progress=on_spider_progress,
            on_spider_done=on_spider_done,
            on_passive_done=on_passive_done,
            on_active_progress=on_active_progress,
            on_active_done=on_active_done,
            on_finding=on_finding,
            console=console,
        )

    return results


# ── Results display ────────────────────────────────────────────────────────────

def show_summary(results):
    console.print()
    _dim_rule()
    console.print()

    summary = results["summary"]
    total = results["total_findings"]

    # Compact stat row
    def _stat(label, count, color):
        t = Text()
        t.append(f"  {count}", style=f"bold {color}")
        t.append(f"  {label}", style="dim white")
        return t

    stats = Text.assemble(
        _stat("High", summary["High"], "red"),
        ("    ", ""),
        _stat("Medium", summary["Medium"], "yellow"),
        ("    ", ""),
        _stat("Low", summary["Low"], "cyan"),
        ("    ", ""),
        _stat("Info", summary["Informational"], "white"),
    )

    console.print(Padding(stats, (0, 2)))
    console.print()

    ts = results["scanned_at"][:19].replace("T", " ")
    console.print(
        f"  [dim]Scanned[/dim]  [white]{results['target_url']}[/white]"
        f"  [dim]·  {ts}[/dim]"
    )
    console.print()

    if total == 0:
        console.print("  [green]✓[/green]  No vulnerabilities confirmed.")
        console.print(
            "  [dim]This doesn't guarantee full security."
            " Try --mode deep for a thorough pass.[/dim]"
        )
    console.print()


def show_findings(results):
    if not results.get("findings"):
        return

    _dim_rule("Findings")
    console.print()

    current_severity = None
    for i, finding in enumerate(results["findings"]):
        sev = finding["severity"]

        if sev != current_severity:
            current_severity = sev
            color = SEVERITY_DOT_COLORS.get(sev, "white")
            console.print(
                f"  [{color}]{SEVERITY_ICONS[sev]}[/{color}]"
                f"  [bold white]{sev}[/bold white]"
            )
            console.print("  " + "─" * 52, style="dim white")

        console.print(
            f"  [dim]{i+1:>3}[/dim]  [white]{finding['vuln_type']}[/white]"
        )
        console.print(f"       [dim]{finding['endpoint'][:70]}[/dim]")
        if finding.get("parameter"):
            console.print(f"       [dim]param  {finding['parameter']}[/dim]")
        console.print()


def show_output_path(path):
    _dim_rule()
    console.print()
    console.print(f"  [dim]Results saved[/dim]  [cyan]{path}[/cyan]")
    console.print()


# ── Entrypoint ─────────────────────────────────────────────────────────────────

def main():
    show_banner()

    url = get_arg("--url")
    if not url:
        console.print("  [bold white]Usage[/bold white]")
        console.print("  [cyan]python main.py --url http://target.com[/cyan]\n")
        sys.exit(1)

    validate_url(url)
    ethics_check(url)

    results = run_scan_with_ui(url)

    os.makedirs("output", exist_ok=True)
    output_file = f"output/{results['scan_id']}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    show_summary(results)
    show_findings(results)
    show_output_path(output_file)


if __name__ == "__main__":
    main()
