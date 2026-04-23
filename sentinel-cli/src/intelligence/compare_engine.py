import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

def compare_scans(dir1: Path, dir2: Path):
    """Compare two scan reports and print a 'Security Diff'."""
    f1 = dir1 / "findings.json"
    f2 = dir2 / "findings.json"
    
    if not f1.exists() or not f2.exists():
        console.print("[red]Findings file missing in one of the scan directories.[/red]")
        return
        
    with open(f1, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    with open(f2, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
        
    findings1 = data1.get("findings", [])
    findings2 = data2.get("findings", [])
    
    # Simple matching based on vuln_type and endpoint
    def get_key(f):
        return f"{f.get('vuln_type')}|{f.get('endpoint')}"
        
    keys1 = {get_key(f): f for f in findings1 if "vuln_type" in f}
    keys2 = {get_key(f): f for f in findings2 if "vuln_type" in f}
    
    fixed = []
    new = []
    persisted = []
    
    for k, f in keys1.items():
        if k not in keys2:
            fixed.append(f)
        else:
            persisted.append(f)
            
    for k, f in keys2.items():
        if k not in keys1:
            new.append(f)
            
    # Print results
    console.print(f"\n[bold white]Scan Comparison[/bold white]")
    console.print(f"[dim]Old: {dir1.name}[/dim]")
    console.print(f"[dim]New: {dir2.name}[/dim]\n")
    
    if not fixed and not new:
        console.print("  [green]✓ No changes detected between scans.[/green]\n")
        return

    if fixed:
        console.print(f"  [bold green]✓ {len(fixed)} Vulnerabilities FIXED[/bold green]")
        for f in fixed:
            console.print(f"    [dim]- {f['vuln_type']} at {f['endpoint'][:50]}[/dim]")
        console.print()

    if new:
        console.print(f"  [bold red]⚠ {len(new)} NEW Vulnerabilities Detected[/bold red]")
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Severity", style="bold")
        table.add_column("Vulnerability")
        table.add_column("Endpoint", style="dim")
        
        for f in new:
            sev = f.get("severity", "Info")
            color = "red" if sev == "High" else "yellow" if sev == "Medium" else "blue"
            table.add_row(f"[{color}]{sev}[/]", f["vuln_type"], f["endpoint"][:50])
        console.print(table)
        console.print()
    
    if persisted:
        console.print(f"  [dim]• {len(persisted)} vulnerabilities remain unchanged.[/dim]\n")
