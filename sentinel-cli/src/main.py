"""
Sentinel CLI — Main Entry Point
Uses Typer for command parsing and Rich for terminal UI.
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Force UTF-8 on Windows to prevent banner crashes
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.text import Text
from rich import box

from src.config import manager as cfg
from src.plugins import manager as plugins_mgr

console = Console()
app = typer.Typer(help="Sentinel Security Scanner — AI-powered pentesting in your terminal.", no_args_is_help=True)

# Sub-apps for grouped commands
config_app = typer.Typer(help="Manage configuration settings")
ollama_app = typer.Typer(help="Local Ollama AI tools")
plugins_app = typer.Typer(help="Manage skill plugins")
zap_app = typer.Typer(help="Manage local ZAP daemon")
report_app = typer.Typer(help="Manage and export scan reports")

app.add_typer(config_app, name="config")
app.add_typer(ollama_app, name="ollama")
app.add_typer(plugins_app, name="plugins")
app.add_typer(zap_app, name="zap")
app.add_typer(report_app, name="report")

# ── UI Helpers ─────────────────────────────────────────────────────────────────

BANNER = """
[bold cyan]  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝[/bold cyan]
"""

def show_banner():
    console.print(BANNER)
    console.print(
        "  [dim white]Ethical Hacking + AI Patch Engine[/dim white]   "
        "[bold green]v0.2.0 — Production Ready[/bold green]\n"
    )

def ethics_check(url: str):
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

def validate_url(url: str):
    if not url.startswith("http"):
        console.print("[red]✗ URL must start with http:// or https://[/red]")
        sys.exit(1)


# ── Core Commands ──────────────────────────────────────────────────────────────

@app.command()
def scan(
    url: str = typer.Option(..., "--url", "-u", help="Target URL to scan"),
    auth_header: Optional[str] = typer.Option(None, "--auth-header", help="Authorization header"),
    login_url: Optional[str] = typer.Option(None, "--login-url", help="Login endpoint for auth scan"),
    request_file: Optional[str] = typer.Option(None, "--request-file", help="Raw HTTP request file"),
    mode: str = typer.Option("deep", "--mode", help="Scan mode: fast | deep | stealth"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip ethics prompt (for automation)")
):
    """Run an AI-orchestrated attack scan."""
    show_banner()
    validate_url(url)
    
    if not yes:
        ethics_check(url)
        
    cfg.log(f"Started {mode} scan on {url}")
    
    provider = cfg.get("ai_provider", "openrouter")
    
    # In a real app we'd load the specific brain
    if provider == "ollama":
        from src.intelligence.ollama_brain import OllamaBrain
        brain = OllamaBrain()
    else:
        from src.intelligence.brain import AttackBrain
        brain = AttackBrain()
        
    results = brain.attack(url, mode=mode, console=console, auth_header=auth_header, login_url=login_url, request_file=request_file)
    
    scan_dir = cfg.new_scan_dir(url)
    findings_file = scan_dir / "findings.json"
    
    with open(findings_file, "w") as f:
        json.dump(results, f, indent=2)
        
    # Write metadata
    meta = {
        "target": url,
        "scanned_at": results.get("scanned_at"),
        "mode": mode,
        "total_findings": results.get("total_findings", 0)
    }
    with open(scan_dir / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
        
    from src.cli.app import show_summary, show_findings
    show_summary(results)
    show_findings(results)
    
    console.print(Rule(style="dim cyan"))
    console.print(f"  [dim]Results saved →[/dim] [cyan]{findings_file}[/cyan]\n")

    if cfg.get("auto_patches"):
        console.print("  [dim]Auto-patch generation enabled...[/dim]")
        # call patches internally...


@app.command()
def patches(
    scan_id: Optional[str] = typer.Argument(None, help="Scan ID to generate patches for (defaults to latest)"),
    format: str = typer.Option("json", "--format", help="Export format: json | md")
):
    """Generate AI fixes for a past scan."""
    show_banner()
    
    scan_dir = None
    if scan_id:
        scan_dir = cfg.get_scan_dir(scan_id)
        if not scan_dir:
            console.print(f"[red]Scan ID '{scan_id}' not found.[/red]")
            raise typer.Exit(1)
    else:
        scan_dir = cfg.latest_scan_dir()
        if not scan_dir:
            console.print("[red]No past scans found.[/red]")
            raise typer.Exit(1)
            
    findings_file = scan_dir / "findings.json"
    if not findings_file.exists():
        console.print(f"[red]No findings.json in {scan_dir}[/red]")
        raise typer.Exit(1)
        
    console.print(f"  [dim]Using scan: {scan_dir.name}[/dim]\n")
        
    from src.patch.engine import generate_patches
    from src.patch.ui import render_patch_ui
    
    with console.status("[bold green]Analyzing scan architecture and generating patches via AI...[/bold green]"):
        try:
            patch_data, summary = generate_patches(str(findings_file))
            
            # Save patches
            with open(scan_dir / "patches.json", "w") as f:
                json.dump(patch_data, f, indent=2)
                
        except Exception as e:
            console.print(f"  [red]Error generating patches: {e}[/red]")
            raise typer.Exit(1)
            
    render_patch_ui(patch_data, summary)
    
    
@app.command()
def chat(scan_id: Optional[str] = typer.Argument(None, help="Scan ID to chat about (defaults to latest)")):
    """Interactive AI chat about your scan results."""
    show_banner()
    
    scan_dir = cfg.get_scan_dir(scan_id) if scan_id else cfg.latest_scan_dir()
    if not scan_dir:
        console.print("[red]Scan not found.[/red]")
        raise typer.Exit(1)
        
    from src.intelligence.chat_engine import interactive_chat
    interactive_chat(scan_dir)


@app.command()
def compare(
    scan_id1: str = typer.Argument(..., help="First Scan ID (e.g. baseline)"),
    scan_id2: str = typer.Argument(..., help="Second Scan ID (e.g. new test)")
):
    """Compare two different scans to track progress."""
    show_banner()
    
    dir1 = cfg.get_scan_dir(scan_id1)
    dir2 = cfg.get_scan_dir(scan_id2)
    
    if not dir1 or not dir2:
        console.print("[red]One or both scan IDs not found.[/red]")
        raise typer.Exit(1)
        
    from src.intelligence.compare_engine import compare_scans
    compare_scans(dir1, dir2)


@app.command()
def history():
    """List all past scans."""
    show_banner()
    scans = cfg.list_scans()
    
    if not scans:
        console.print("  [dim]No scans found.[/dim]")
        return
        
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Scan ID", style="cyan")
    table.add_column("Target", style="white")
    table.add_column("Date", style="dim")
    table.add_column("Findings", justify="right")
    
    for s in scans:
        date_str = s.get("scanned_at", "")[:16].replace("T", " ")
        table.add_row(
            s.get("_id", ""),
            s.get("target", "Unknown"),
            date_str,
            str(s.get("total_findings", 0))
        )
        
    console.print(table)


@app.command()
def doctor():
    """Health check: ZAP, Ollama, API keys, dependencies."""
    show_banner()
    console.print("[bold white]System Health Check[/bold white]\n")
    
    # 1. Config directory
    cfg_ok = cfg.SENTINEL_HOME.exists()
    console.print(f"  [{'green' if cfg_ok else 'red'}]{'✓' if cfg_ok else '✗'}[/] Config dir: {cfg.SENTINEL_HOME}")
    
    # 2. ZAP
    try:
        import requests
        zap_url = cfg.zap_url()
        r = requests.get(f"{zap_url}/JSON/core/view/version", timeout=3)
        zap_ok = r.status_code == 200
        zap_ver = r.json().get('version', 'unknown') if zap_ok else ""
        console.print(f"  [{'green' if zap_ok else 'red'}]{'✓' if zap_ok else '✗'}[/] ZAP Daemon: {zap_url} (v{zap_ver})")
    except Exception:
        console.print(f"  [red]✗[/red] ZAP Daemon: unreachable at {cfg.zap_url()}")
        
    # 3. Ollama
    try:
        ollama_host = cfg.get("ollama_host")
        r = requests.get(f"{ollama_host}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
        console.print(f"  [{'green' if ollama_ok else 'yellow'}]{'✓' if ollama_ok else '!'}[/] Ollama AI:  {ollama_host}")
    except Exception:
        console.print(f"  [yellow]![/yellow] Ollama AI:  unreachable at {cfg.get('ollama_host')} (Local AI disabled)")
        
    # 4. OpenRouter API Key
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    key_ok = bool(or_key and or_key.startswith("sk-or-"))
    console.print(f"  [{'green' if key_ok else 'yellow'}]{'✓' if key_ok else '!'}[/] OpenRouter: {'Configured' if key_ok else 'Missing API Key'}")
    
    # 5. Binaries
    import shutil
    for binary in ["docker", "java", "nuclei", "subfinder"]:
        bin_ok = shutil.which(binary) is not None
        console.print(f"  [{'green' if bin_ok else 'yellow'}]{'✓' if bin_ok else '!'}[/] Binary:     {binary}")

    console.print()


# ── Config Commands ────────────────────────────────────────────────────────────

@config_app.command("set")
def config_set(key: str, value: str):
    """Set a configuration value."""
    try:
        cfg.set(key, value)
        console.print(f"[green]✓ Config updated:[/green] {key} = {value}")
    except KeyError as e:
        console.print(f"[red]✗ {e}[/red]")

@config_app.command("show")
def config_show():
    """Show current configuration."""
    settings = cfg.all_settings()
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Description", style="dim")
    
    for k, v in settings.items():
        desc = cfg.CONFIG_DESCRIPTIONS.get(k, "")
        table.add_row(k, str(v), desc)
        
    console.print(table)


# ── Ollama Commands ────────────────────────────────────────────────────────────

@ollama_app.command("check")
def ollama_check(url: str = typer.Argument(..., help="Target URL")):
    """Run a local, offline vulnerability scan using Ollama."""
    show_banner()
    validate_url(url)
    
    from src.intelligence.ollama_brain import OllamaBrain
    try:
        brain = OllamaBrain()
        results = brain.attack(url, console=console)
        
        scan_dir = cfg.new_scan_dir(url)
        with open(scan_dir / "findings.json", "w") as f:
            json.dump(results, f, indent=2)
            
        from src.cli.app import show_summary, show_findings
        show_summary(results)
        show_findings(results)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@ollama_app.command("models")
def ollama_models():
    """List available local Ollama models."""
    from src.intelligence.ollama_brain import OllamaBrain
    try:
        brain = OllamaBrain()
        models = brain.list_models()
        if not models:
            console.print("No models found in Ollama.")
            return
            
        console.print("[bold white]Local Ollama Models:[/bold white]\n")
        for m in models:
            console.print(f"  • [cyan]{m['name']}[/cyan] [dim]({m.get('details', {}).get('parameter_size', '?')})[/dim]")
        console.print(f"\n[dim]Set active model with: sentinel config set ollama_model <name>[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@ollama_app.command("set-model")
def ollama_set_model(model: str):
    """Set the default Ollama model."""
    cfg.set("ollama_model", model)
    console.print(f"[green]✓ Ollama model set to: {model}[/green]")


# ── Plugins Commands ───────────────────────────────────────────────────────────

@plugins_app.command("list")
def plugins_list():
    """List available and installed plugins."""
    plugins = plugins_mgr.list_plugins()
    
    table = Table(box=box.SIMPLE)
    table.add_column("Plugin", style="cyan")
    table.add_column("Installed", justify="center")
    table.add_column("Binary OK", justify="center")
    table.add_column("Version", style="dim")
    table.add_column("Description")
    
    for p in plugins:
        inst = "[green]✓[/green]" if p['installed'] else "[dim]-[/dim]"
        bin_ok = "[green]✓[/green]" if p['binary_ok'] else "[red]✗[/red]"
        if not p['binary']:
            bin_ok = "[dim]-[/dim]"
            
        table.add_row(
            p['name'], inst, bin_ok, str(p['version']), p['description']
        )
        
    console.print(table)


@plugins_app.command("install")
def plugins_install(name: str):
    """Install a plugin."""
    success, msg = plugins_mgr.install(name)
    if success:
        console.print(f"[green]✓ {msg}[/green]")
    else:
        console.print(f"[red]✗ {msg}[/red]")


@plugins_app.command("run")
def plugins_run(name: str, url: str = typer.Option(..., "--url", "-u")):
    """Run a specific plugin against a target."""
    validate_url(url)
    console.print(f"Running plugin [cyan]{name}[/cyan] against [cyan]{url}[/cyan]...\n")
    try:
        findings = plugins_mgr.run_plugin(name, url, console=console)
        if not findings:
            console.print("  [dim]✓ No findings.[/dim]")
            return
            
        for f in findings:
            from src.cli.app import SEVERITY_COLORS, SEVERITY_ICONS
            sev = f.get("severity", "Informational")
            color = SEVERITY_COLORS.get(sev, "white")
            icon = SEVERITY_ICONS.get(sev, "•")
            
            console.print(
                f"  {icon} [{color}]{sev:<14}[/{color}] "
                f"[white]{f.get('vuln_type', '')}[/white]  "
                f"[dim]{f.get('endpoint', '')[:50]}[/dim]"
            )
            
    except Exception as e:
        console.print(f"[red]Error running plugin {name}:[/red] {e}")


def main():
    """CLI entry point. If no args, drops into interactive REPL."""
    if len(sys.argv) == 1:
        from src.cli.shell import interactive_loop
        interactive_loop()
    else:
        app()

if __name__ == "__main__":
    main()