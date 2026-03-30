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
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.rule import Rule
from rich import box

console = Console()

BANNER = """
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
"""

SEVERITY_COLORS = {
    "High":          "bold red",
    "Medium":        "bold yellow",
    "Low":           "bold blue",
    "Informational": "dim white",
}

SEVERITY_ICONS = {
    "High":          "🔴",
    "Medium":        "🟠",
    "Low":           "🔵",
    "Informational": "⚪",
}

def show_banner():
    console.print(BANNER, style="bold cyan")
    console.print(
        "  Ethical Hacking + AI Patch Engine   "
        "v0.1 — Attack Engine\n",
        style="dim white"
    )
    console.print(Rule(style="dim cyan"))

def get_arg(flag):
    try:
        idx = sys.argv.index(flag)
        return sys.argv[idx + 1]
    except (ValueError, IndexError):
        return None

def ethics_check(url):
    console.print()
    console.print(Panel(
        f"[bold white]Target[/bold white]\n"
        f"[cyan]  {url}[/cyan]\n\n"
        f"[yellow]⚠  By proceeding you confirm:[/yellow]\n"
        f"[dim]  • You own this target, or\n"
        f"  • You have explicit written permission to test it\n\n"
        f"  Unauthorized scanning is illegal and may result\n"
        f"  in criminal charges.[/dim]",
        border_style="yellow",
        title="[yellow]Ethics Disclaimer[/yellow]",
        width=60
    ))
    console.print()
    confirm = console.input("  [bold white]Type [green]YES[/green] to confirm and start scan:[/bold white] ")
    if confirm.strip().upper() != "YES":
        console.print("\n  [red]✗ Scan cancelled.[/red]\n")
        sys.exit(0)
    console.print()

def validate_url(url):
    blocked = ["localhost", "127.0.0.1", "192.168.", "10.", "172.16.", "0.0.0.0"]
    # Allow localhost only for testing
    if not url.startswith("http"):
        console.print("[red]✗ URL must start with http:// or https://[/red]")
        sys.exit(1)

def print_finding(finding, index):
    severity = finding["severity"]
    color = SEVERITY_COLORS.get(severity, "white")
    icon = SEVERITY_ICONS.get(severity, "•")
    
    console.print(
        f"  {icon}  [{color}]{severity:<14}[/{color}] "
        f"[white]{finding['vuln_type']}[/white]  "
        f"[dim]{finding['endpoint'][:50]}[/dim]"
    )

def show_summary(results):
    console.print()
    console.print(Rule(style="dim cyan"))
    console.print()
    console.print("  [bold white]Scan Complete[/bold white]", end="")
    console.print(f"  [dim]·  {results['scanned_at'][:19].replace('T', ' ')}[/dim]")
    console.print(f"  [dim]    {results['target_url']}[/dim]")
    console.print()

    # Summary boxes
    summary = results["summary"]
    total = results["total_findings"]

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column(width=16)
    table.add_column(width=8)
    table.add_column(width=16)
    table.add_column(width=8)

    table.add_row(
        "[bold red]🔴 High[/bold red]",
        f"[bold red]{summary['High']}[/bold red]",
        "[bold yellow]🟠 Medium[/bold yellow]",
        f"[bold yellow]{summary['Medium']}[/bold yellow]",
    )
    table.add_row(
        "[bold blue]🔵 Low[/bold blue]",
        f"[bold blue]{summary['Low']}[/bold blue]",
        "[dim]⚪ Info[/dim]",
        f"[dim]{summary['Informational']}[/dim]",
    )

    console.print(table)
    console.print(f"  [dim]Total findings: {total}[/dim]")
    console.print()

def show_findings(results):
    console.print(Rule("Findings", style="dim cyan"))
    console.print()

    current_severity = None
    for i, finding in enumerate(results["findings"]):
        if finding["severity"] != current_severity:
            current_severity = finding["severity"]
            color = SEVERITY_COLORS.get(current_severity, "white")
            icon = SEVERITY_ICONS.get(current_severity, "•")
            console.print(f"\n  [{color}]{icon} {current_severity}[/{color}]")
            console.print(f"  {'─' * 50}", style="dim")

        console.print(
            f"  [dim]{i+1:>3}.[/dim]  "
            f"[white]{finding['vuln_type']}[/white]"
        )
        console.print(
            f"        [dim]{finding['endpoint'][:70]}[/dim]"
        )
        if finding.get("parameter"):
            console.print(
                f"        [dim]param: {finding.get('parameter')}[/dim]"
            )

    console.print()

def show_output_path(path):
    console.print(Rule(style="dim cyan"))
    console.print()
    console.print(f"  [dim]Results saved →[/dim] [cyan]{path}[/cyan]")
    console.print()

def run_scan_with_ui(url, auth_header=None, login_url=None, request_file=None):
    from src.attack.zap_scanner import run_zap_scan_live

    findings_so_far = []
    results_container = {}

    console.print(Rule("Attack Engine", style="dim cyan"))
    console.print()

    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=30, style="dim cyan", complete_style="cyan"),
        TextColumn("[dim]{task.fields[status]}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:

        spider_task = progress.add_task(
            "Spider       ", total=100, status="starting..."
        )
        passive_task = progress.add_task(
            "Passive Scan ", total=100, status="waiting..."
        )
        active_task = progress.add_task(
            "Active Scan  ", total=100, status="waiting..."
        )

        def on_spider_progress(pct):
            progress.update(spider_task, completed=pct, status=f"{pct}%")

        def on_spider_done(url_count):
            progress.update(spider_task, completed=100, status=f"✓ {url_count} URLs")

        def on_passive_done():
            progress.update(passive_task, completed=100, status="✓ done")

        def on_active_progress(pct):
            progress.update(active_task, completed=pct, status=f"{pct}%")

        def on_active_done():
            progress.update(active_task, completed=100, status="✓ done")

        def on_finding(finding):
            findings_so_far.append(finding)
            severity = finding["severity"]
            color = SEVERITY_COLORS.get(severity, "white")
            icon = SEVERITY_ICONS.get(severity, "•")
            progress.console.print(
                f"  {icon} [{color}]{severity:<14}[/{color}] "
                f"[white]{finding['vuln_type']}[/white]  "
                f"[dim]{finding['endpoint'][:45]}[/dim]"
            )

        from src.intelligence.brain import AttackBrain
        brain = AttackBrain()
        results = brain.attack(url, console=console, auth_header=auth_header, login_url=login_url, request_file=request_file)


    return results

def main():
    if len(sys.argv) < 2:
        from src.cli.repl import interactive_loop
        interactive_loop()
        return

    command = sys.argv[1].lower()

    if command == "scan":
        show_banner()
        url = get_arg("--url")
        if not url:
            console.print()
            console.print("  [bold white]Usage:[/bold white]")
            console.print("  [cyan]sentinel scan --url http://target.com[/cyan]")
            console.print()
            sys.exit(1)

        auth_header = get_arg("--auth-header")
        login_url = get_arg("--login-url")
        request_file = get_arg("--request-file")

        validate_url(url)
        ethics_check(url)

        results = run_scan_with_ui(url, auth_header, login_url, request_file)

        os.makedirs("output", exist_ok=True)
        output_file = f"output/{results['scan_id']}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        show_summary(results)
        show_findings(results)
        show_output_path(output_file)

    elif command == "patches":
        show_banner()
        target_file = None
        if len(sys.argv) > 2 and sys.argv[2].endswith('.json'):
            target_file = sys.argv[2]
        else:
            output_dir = os.path.join(os.getcwd(), 'output')
            if os.path.exists(output_dir):
                files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.json')]
                if files:
                    target_file = max(files, key=os.path.getctime)
                    console.print(f"  [dim]Auto-selected latest scan: {target_file}[/dim]\n")
        
        if not target_file:
            console.print("  [red]No scan file provided and none found in output directory.[/red]")
            sys.exit(1)
            
        from src.patch.engine import generate_patches
        from src.patch.ui import render_patch_ui
        
        with console.status("[bold green]Analyzing scan architecture and generating patches via Groq...[/bold green]"):
            try:
                patch_data, summary = generate_patches(target_file)
            except Exception as e:
                console.print(f"  [red]Error generating patches: {e}[/red]")
                sys.exit(1)
                
        render_patch_ui(patch_data, summary)
        
    else:
        # Drop into interactive shell for any unrecognized startup command
        from src.cli.repl import interactive_loop
        interactive_loop()

if __name__ == "__main__":
    main()