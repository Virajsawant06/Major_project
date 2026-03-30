from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns

console = Console()

def render_patch_ui(patch_data, counts):
    """
    Renders the exact UI specified in the user's reference image for patches.
    """
    _render_stat_bar(counts)
    
    # Bottom line
    bottom_line = Text("Bottom line: ", style="bold #2c3e50")
    bottom_line.append(patch_data.get('summary_bottom_line', 'Scan complete. '), style="#2c3e50")
    bottom_line.append(patch_data.get('estimated_total_time', ''), style="bold #27ae60")
    
    console.print(Panel(bottom_line, style="on #eaf2f8", border_style="#eaf2f8", padding=(1, 2)))
    console.print()
    
    console.print("[dim bold]WHAT TO FIX[/dim bold]")
    
    for issue in patch_data.get("issues", []):
        _render_issue_card(issue)

def _render_stat_bar(counts):
    console.print()
    
    # Check severity
    high_count = counts.get("High", 0)
    c_high = "#27ae60" if high_count == 0 else "#c0392b"
    
    t_high = Text(f"\n{high_count}\n", style=f"bold white on {c_high}", justify="center")
    t_high.append("HIGH\n", style=f"bold white on {c_high}")
    
    c_med = "#e67e22"
    t_med = Text(f"\n{counts.get('Medium', 0)}\n", style=f"bold white on {c_med}", justify="center")
    t_med.append("MEDIUM\n", style=f"bold white on {c_med}")
    
    c_low = "#2980b9"
    t_low = Text(f"\n{counts.get('Low', 0)}\n", style=f"bold white on {c_low}", justify="center")
    t_low.append("LOW\n", style=f"bold white on {c_low}")
    
    total = sum([counts.get(k, 0) for k in ["High", "Medium", "Low", "Informational"]])
    c_tot = "#2c3e50"
    t_tot = Text(f"\n{total}\n", style=f"bold white on {c_tot}", justify="center")
    t_tot.append("TOTAL\n", style=f"bold white on {c_tot}")
    
    cols = Columns([
        Panel(t_high, style=f"on {c_high}", border_style=c_high, width=18),
        Panel(t_med,  style=f"on {c_med}",  border_style=c_med,  width=18),
        Panel(t_low,  style=f"on {c_low}",  border_style=c_low,  width=18),
        Panel(t_tot,  style=f"on {c_tot}",  border_style=c_tot,  width=18)
    ], padding=(0, 0))
    console.print(cols)
    console.print()

def _render_issue_card(issue):
    sev = issue.get("severity", "LOW").upper()
    title = issue.get("title", "Unknown vulnerability")
    time_fix = issue.get("fix_time", "Fix quickly")
    
    # Background colors for specific severities
    if sev == "HIGH": bg_col = "#c0392b"
    elif sev == "MEDIUM": bg_col = "#d35400"
    else: bg_col = "#2980b9"
    
    # HEADER
    head_txt = Text(f"*  {title} ", style=f"bold white on {bg_col}")
    head_txt.append(f" · {sev}  · {time_fix}", style=f"dim white on {bg_col}")
    console.print(Panel(head_txt, style=f"on {bg_col}", border_style=bg_col, padding=(0, 1)))
    
    # CONTEXT
    body = Text("Does it affect you right now?\n", style="bold #2c3e50")
    body.append(issue.get("affects_now", "Yes."), style="#2c3e50")
    # White background with dark text
    console.print(Panel(body, style="on white", border_style="white", padding=(1, 2)))
    
    # PASTE FIX (Code block)
    fix_head = Text("Paste this fix:\n", style="bold #27ae60")
    # Actually the image has dark green code snippet text on a light green background
    fix_body = Text(issue.get("paste_fix", ""), style="bold #16a085")
    fix_head.append(fix_body)
    
    console.print(Panel(fix_head, style="on #eafaf1", border_style="#eafaf1", padding=(1, 2)))
    console.print()
