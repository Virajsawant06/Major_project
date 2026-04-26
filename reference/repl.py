"""
Sentinel · Simple REPL
A lightweight interactive loop used when prompt_toolkit is unavailable.
Mirrors the shell.py experience using only Rich + stdlib.
"""

import sys
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

console = Console()

# ── Help ───────────────────────────────────────────────────────────────────────

def _show_help() -> None:
    console.print()
    console.print(Rule("[dim]Commands[/dim]", style="dim white"))
    console.print()

    tbl = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    tbl.add_column(min_width=10, style="cyan bold")
    tbl.add_column(min_width=14, style="dim white")
    tbl.add_column(style="white")

    rows = [
        ("scan",    "<url>",        "Launch full attack timeline against a target"),
        ("patches", "[file]",       "Generate AI fixes (auto-picks latest scan)"),
        ("help",    "",             "Show this message"),
        ("exit",    "",             "Quit"),
    ]
    for cmd, args, desc in rows:
        tbl.add_row(cmd, args, desc)

    console.print(tbl)
    console.print()


# ── REPL loop ──────────────────────────────────────────────────────────────────

def interactive_loop() -> None:
    from src.main import show_banner

    show_banner()
    _show_help()

    while True:
        try:
            raw = Prompt.ask("\n[bold cyan]sentinel[/bold cyan] [dim]❯[/dim]")
            text = raw.strip()
            if not text:
                continue

            parts = text.split()
            base = parts[0].lower()

            # ── exit ───────────────────────────────────────────────────────────
            if base in ("exit", "quit", "q"):
                console.print("\n  [dim]Goodbye.[/dim]\n")
                break

            # ── help ───────────────────────────────────────────────────────────
            elif base == "help":
                _show_help()

            # ── scan ───────────────────────────────────────────────────────────
            elif base == "scan":
                target = parts[1] if len(parts) > 1 else Prompt.ask("  [white]Target URL[/white]")
                if not target.startswith("http"):
                    target = "http://" + target

                console.print(f"\n  [dim]Starting scanner for[/dim] [cyan]{target}[/cyan]…\n")
                os.system(f"sentinel.bat scan --url {target}")

            # ── patches ────────────────────────────────────────────────────────
            elif base == "patches":
                target_file = None

                if len(parts) > 1 and parts[-1].endswith(".json"):
                    target_file = parts[-1]
                else:
                    output_dir = os.path.join(os.getcwd(), "output")
                    if os.path.exists(output_dir):
                        files = [
                            os.path.join(output_dir, f)
                            for f in os.listdir(output_dir)
                            if f.endswith(".json")
                        ]
                        if files:
                            target_file = max(files, key=os.path.getctime)
                            console.print(f"  [dim]Using latest scan:[/dim] [cyan]{target_file}[/cyan]")
                        else:
                            console.print("  [red]✗[/red]  No scans found in [cyan]output/[/cyan]. Run a scan first.")
                            continue
                    else:
                        console.print("  [red]✗[/red]  Output directory not found. Run a scan first.")
                        continue

                from src.patch.engine import generate_patches
                from src.patch.ui import render_patch_ui

                with console.status(
                    "[cyan]Analyzing findings and generating patches…[/cyan]",
                    spinner="dots",
                ):
                    try:
                        patch_data, summary = generate_patches(target_file)
                    except Exception as e:
                        console.print(f"  [red]✗[/red]  Patch generation failed: {e}")
                        continue

                render_patch_ui(patch_data, summary)

            # ── unknown ────────────────────────────────────────────────────────
            else:
                console.print(f"  [red]✗[/red]  Unknown command: [white]{base}[/white]")
                _show_help()

        except KeyboardInterrupt:
            console.print()
            console.print("  [dim]Use [white]exit[/white] to quit.[/dim]")
        except EOFError:
            console.print("\n  [dim]Goodbye.[/dim]\n")
            break
