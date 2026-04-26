"""
Sentinel Interactive Shell
A Claude Code-style REPL with command history, tab completion,
live prompt, and clean command dispatch.
"""

import sys
import shlex
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich.text import Text
from rich import box

from src.config import manager as cfg

console = Console()

# ── Command registry ───────────────────────────────────────────────────────────

COMMANDS = [
    "scan", "patches", "ollama", "config", "history", "report",
    "zap", "doctor", "update", "plugins", "chat", "compare", "schedule",
    "exit", "quit", "help", "clear", "cls",
]

_HELP_TABLE = [
    # (command,              args hint,      description)
    ("scan",      "--url <url>",    "Run a full attack timeline against a target"),
    ("chat",      "[scan_id]",      "AI chat about a specific scan result"),
    ("patches",   "[scan_id]",      "Generate and display AI-written fixes"),
    ("compare",   "<id1> <id2>",    "Diff two scans to track remediation progress"),
    ("history",   "",               "List past scans with status and findings"),
    ("report",    "[scan_id]",      "Export a scan to PDF / HTML"),
    ("plugins",   "list|install",   "Manage installed security skill modules"),
    ("ollama",    "check <url>",    "Offline analysis using a local Ollama model"),
    ("config",    "show|set",       "View or update system settings"),
    ("doctor",    "",               "Health-check ZAP, Ollama, API keys"),
    ("clear",     "",               "Clear the terminal"),
    ("exit",      "",               "Quit Sentinel"),
]

_prompt_style = Style.from_dict({
    "brand":    "#00d7ff bold",
    "model":    "#555555",
    "arrow":    "#00d7ff",
})


# ── Help renderer ──────────────────────────────────────────────────────────────

def _show_help() -> None:
    console.print()
    console.print(Rule("[dim]Commands[/dim]", style="dim white"))
    console.print()

    tbl = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    tbl.add_column(min_width=10, style="cyan bold")
    tbl.add_column(min_width=16, style="dim white")
    tbl.add_column(style="white")

    for cmd, args, desc in _HELP_TABLE:
        tbl.add_row(cmd, args, desc)

    console.print(tbl)
    console.print()


# ── Shell loop ─────────────────────────────────────────────────────────────────

def interactive_loop() -> None:
    cfg._ensure_dirs()
    history_file = cfg.SENTINEL_HOME / ".history"

    completer = FuzzyCompleter(WordCompleter(COMMANDS, ignore_case=True))

    session = PromptSession(
        history=FileHistory(str(history_file)),
        completer=completer,
        style=_prompt_style,
        mouse_support=False,
    )

    from src.main import show_banner, app

    os.system("cls" if os.name == "nt" else "clear")
    show_banner()
    console.print("  [dim]Type [white]help[/white] to see commands · [white]exit[/white] to quit[/dim]\n")

    while True:
        try:
            # Dynamic prompt reflects active AI model
            ai_provider = cfg.get("ai_provider", "openrouter")
            if ai_provider == "ollama":
                model = cfg.get("ollama_model", "ollama")
            else:
                model = cfg.get("openrouter_model", "cloud")

            prompt_tokens = HTML(
                f'<brand>sentinel</brand>'
                f' <model>[{model}]</model>'
                f' <arrow>❯</arrow> '
            )

            raw = session.prompt(prompt_tokens, style=_prompt_style)
            text = raw.strip()
            if not text:
                continue

            # ── Built-ins ──────────────────────────────────────────────────────
            if text.lower() in ("exit", "quit", "q"):
                console.print("\n  [dim]Goodbye.[/dim]\n")
                break

            if text.lower() in ("clear", "cls"):
                os.system("cls" if os.name == "nt" else "clear")
                show_banner()
                continue

            if text.lower() == "help":
                _show_help()
                continue

            # ── Typer dispatch ─────────────────────────────────────────────────
            try:
                args = shlex.split(text)
            except ValueError as e:
                console.print(f"  [red]Parse error:[/red] {e}")
                continue

            try:
                app(args, standalone_mode=False)
            except SystemExit:
                # Typer raises SystemExit on --help or bad args; swallow it.
                pass
            except Exception as e:
                console.print(f"  [red]Error:[/red] {e}")

        except KeyboardInterrupt:
            # Ctrl-C cancels current input line without exiting
            console.print()
            continue
        except EOFError:
            # Ctrl-D exits cleanly
            console.print("\n  [dim]Goodbye.[/dim]\n")
            break
