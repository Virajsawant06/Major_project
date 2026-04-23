"""
Sentinel Interactive Shell
Provides a 'claude code'-like experience with command history, 
tab completion, and colored prompts.
"""

import sys
import shlex
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from rich.console import Console

from src.config import manager as cfg

console = Console()

COMMANDS = [
    "scan", "patches", "ollama", "config", "history", "report", 
    "zap", "doctor", "update", "plugins", "chat", "compare", "schedule",
    "exit", "quit", "help", "clear", "cls"
]

completer = WordCompleter(COMMANDS, ignore_case=True)

def interactive_loop():
    """Run the interactive REPL."""
    # Ensure config dir exists for history
    cfg._ensure_dirs()
    history_file = cfg.SENTINEL_HOME / ".history"
    
    session = PromptSession(
        history=FileHistory(str(history_file)),
        completer=completer
    )

    from src.main import show_banner, app
    
    # We want to clear screen and show banner
    os.system('cls' if os.name == 'nt' else 'clear')
    show_banner()
    console.print("[dim]Type 'help' to see available commands or 'exit' to quit.[/dim]\n")

    while True:
        try:
            # We want prompt to reflect current state, e.g. active model
            ai_model = cfg.get("ollama_model") if cfg.get("ai_provider") == "ollama" else cfg.get("openrouter_model")
            prompt_html = HTML(f'<ansicyan>sentinel</ansicyan> <ansidarkgray>[{ai_model}]</ansidarkgray> ❯ ')
            
            text = session.prompt(prompt_html)
            
            text = text.strip()
            if not text:
                continue
                
            if text.lower() in ['exit', 'quit']:
                console.print("[dim]Goodbye.[/dim]")
                break
                
            if text.lower() in ['clear', 'cls']:
                os.system('cls' if os.name == 'nt' else 'clear')
                show_banner()
                continue
                
            if text.lower() == 'help':
                # Quick help inside repl
                console.print("\n  [bold white]Available Interactive Commands:[/bold white]")
                console.print("  [cyan]scan --url <url>[/cyan]     [dim]• Launch full attack timeline (fast/deep mode)[/dim]")
                console.print("  [cyan]chat [scan_id][/cyan]       [dim]• Interactive AI chat about your scan results[/dim]")
                console.print("  [cyan]patches [scan_id][/cyan]    [dim]• Generate AI fixes for a scan[/dim]")
                console.print("  [cyan]compare <id1> <id2>[/cyan] [dim]• Compare two different scans to track progress[/dim]")
                console.print("  [cyan]plugins list[/cyan]         [dim]• View installed security plugins[/dim]")
                console.print("  [cyan]plugins install[/cyan]      [dim]• Install a new security skill[/dim]")
                console.print("  [cyan]ollama check <url>[/cyan]   [dim]• Offline local scan using Ollama[/dim]")
                console.print("  [cyan]config show[/cyan]          [dim]• View system settings[/dim]")
                console.print("  [cyan]history[/cyan]              [dim]• View past scans[/dim]")
                console.print("  [cyan]doctor[/cyan]               [dim]• Check system health[/dim]")
                console.print("  [cyan]clear[/cyan]                [dim]• Clear screen[/dim]")
                console.print("  [cyan]exit[/cyan]                 [dim]• Close interactive shell[/dim]\n")
                continue

            # Parse arguments like a real shell
            try:
                args = shlex.split(text)
            except ValueError as e:
                console.print(f"[red]Error parsing command: {e}[/red]")
                continue
                
            # Hand off to typer app. 
            # We catch SystemExit so Typer doesn't kill our REPL on error/help
            try:
                app(args, standalone_mode=False)
            except SystemExit as e:
                # Typer raises SystemExit(0) for successful --help
                # and SystemExit(2) for invalid args. We ignore them here.
                pass
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                
        except KeyboardInterrupt:
            continue  # Control-C cancels current line
        except EOFError:
            break  # Control-D exits

