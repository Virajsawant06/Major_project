import sys
import os

from rich.console import Console
from rich.prompt import Prompt

console = Console()

def _show_help():
    console.print("\n  [bold white]Available Interactive Commands:[/bold white]")
    console.print("  [cyan]scan <url>[/cyan]     [dim]• Launch full attack timeline (Automatically boots ZAP)[/dim]")
    console.print("  [cyan]patches [file][/cyan]   [dim]• Generate AI fixes for a scan (auto-picks latest if omitted)[/dim]")
    console.print("  [cyan]exit[/cyan]           [dim]• Close interactive shell[/dim]")
    console.print()

def interactive_loop():
    # Import locally because main.py uses this and we don't want circular imports
    from src.main import show_banner
    
    show_banner()
    _show_help()
    
    while True:
        try:
            cmd = Prompt.ask("\n[bold cyan]Sentinel >[/bold cyan]")
            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd.lower() in ["exit", "quit", "q"]:
                break
                
            parts = cmd.split()
            base = parts[0].lower()
            
            if base == "scan":
                # For an interactive scan, it is easiest to re-invoke the .bat file 
                # so the ZAP daemon boots natively in the external command window
                if len(parts) > 1:
                    target = parts[-1]
                else:
                    target = Prompt.ask("[bold white]Enter target URL[/bold white]")
                
                if not target.startswith("http"):
                    target = "http://" + target
                
                # Execute the wrapper command
                console.print(f"[dim]Invoking Sentinel Scanner process for {target}...[/dim]\n")
                os.system(f"sentinel.bat scan --url {target}")
                
            elif base == "patches":
                target_file = None
                # If they passed an explicit file
                if len(parts) > 1 and parts[-1].endswith(".json"):
                    target_file = parts[-1]
                else:
                    # Automatically find the latest JSON file in output/
                    output_dir = os.path.join(os.getcwd(), 'output')
                    if os.path.exists(output_dir):
                        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.json')]
                        if files:
                            latest_file = max(files, key=os.path.getctime)
                            target_file = latest_file
                            console.print(f"[dim]Auto-selected latest scan: {target_file}[/dim]")
                        else:
                            console.print("[red]No scan outputs found in output/ directory. Run a scan first![/red]")
                            continue
                    else:
                        console.print("[red]Output directory not found. Run a scan first![/red]")
                        continue
                        
                from src.patch.engine import generate_patches
                from src.patch.ui import render_patch_ui
                
                with console.status("[bold green]Analyzing scan architecture and generating patches via Groq...[/bold green]"):
                    try:
                        patch_data, summary = generate_patches(target_file)
                    except Exception as e:
                        console.print(f"[red]Error generating patches: {e}[/red]")
                        continue
                
                render_patch_ui(patch_data, summary)
                
            elif base == "help":
                _show_help()
            else:
                console.print(f"[red]Unknown command:[/red] {base}")
                _show_help()
                
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit.[/dim]")
        except EOFError:
            break
