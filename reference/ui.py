"""
Sentinel · Patch UI
Renders AI-generated patch results in a clean, structured terminal layout
inspired by Claude Code / Gemini CLI aesthetics.
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from rich.padding import Padding
from rich.columns import Columns
from rich.align import Align
from rich.syntax import Syntax

console = Console()

# ── Color palette ──────────────────────────────────────────────────────────────

_SEV_COLOR = {
    "HIGH":   "red",
    "MEDIUM": "yellow",
    "LOW":    "cyan",
    "INFO":   "white",
}

_SEV_ICON = {
    "HIGH":   "●",
    "MEDIUM": "●",
    "LOW":    "●",
    "INFO":   "○",
}


# ── Public entry point ─────────────────────────────────────────────────────────

def render_patch_ui(patch_data: dict, counts: dict) -> None:
    """Render the full patch report to the terminal."""
    console.print()
    _render_header(patch_data, counts)
    console.print()

    issues = patch_data.get("issues", [])
    if not issues:
        console.print("  [green]✓[/green]  No actionable issues to patch.\n")
        return

    console.print(
        "  [dim]What to fix[/dim]"
        f"  [white]{len(issues)} issue{'s' if len(issues) != 1 else ''}[/white]\n"
    )

    for idx, issue in enumerate(issues, 1):
        _render_issue(issue, idx, total=len(issues))

    _render_footer(patch_data)


# ── Internal renderers ─────────────────────────────────────────────────────────

def _render_header(patch_data: dict, counts: dict) -> None:
    """Top stat bar + summary sentence."""
    console.print(Rule(style="dim white"))
    console.print()

    # Stat pills
    panels = []
    for key in ("High", "Medium", "Low", "Informational"):
    
        label = "INFO" if key == "Informational" else key.upper()
        color = _SEV_COLOR.get(label, "white")
        count = counts.get(key, 0)

        content = Text(justify="center")
        content.append(f"\n{count}\n", style=f"bold white")
        content.append(f"{label}\n", style=f"bold {color}")

        panels.append(
            Panel(
                Align.center(content),
                border_style=color if count > 0 else "dim white",
                width=16,
                padding=(0, 1),
            )
        )

    console.print(Padding(Columns(panels, padding=(0, 1)), pad=(0, 2)))
    console.print()

    # Bottom-line summary
    summary = patch_data.get("summary_bottom_line", "")
    eta = patch_data.get("estimated_total_time", "")
    if summary:
        line = Text("  ")
        line.append("Summary  ", style="dim white")
        line.append(summary, style="white")
        if eta:
            line.append(f"  ·  {eta}", style="green")
        console.print(line)


def _render_issue(issue: dict, idx: int, total: int) -> None:
    """Render a single issue card: header + context + fix."""
    sev = issue.get("severity", "LOW").upper()
    color = _SEV_COLOR.get(sev, "white")
    icon = _SEV_ICON.get(sev, "●")
    title = issue.get("title", "Unknown vulnerability")
    fix_time = issue.get("fix_time", "")

    # ── Issue header line ──────────────────────────────────────────────────────
    header = Text()
    header.append(f"  [{idx}/{total}]  ", style="dim white")
    header.append(f"{icon} ", style=color)
    header.append(title, style="bold white")
    if sev:
        header.append(f"  {sev}", style=color)
    if fix_time:
        header.append(f"  ·  {fix_time}", style="dim white")

    console.print(header)
    console.print("  " + "─" * 60, style="dim white")

    # ── Context block ──────────────────────────────────────────────────────────
    affects = issue.get("affects_now", "")
    if affects:
        console.print()
        console.print("  [dim]Does it affect you right now?[/dim]")
        console.print(f"  [white]{affects}[/white]")

    # ── Fix block ──────────────────────────────────────────────────────────────
    paste_fix = issue.get("paste_fix", "")
    if paste_fix:
        console.print()
        console.print("  [dim]Paste this fix[/dim]")
        console.print()

        # Detect language hint inside fix (e.g. starts with "#!" or looks like code)
        lang = _detect_lang(paste_fix)
        syntax = Syntax(
            paste_fix,
            lang,
            theme="ansi_dark",
            background_color="default",
            word_wrap=True,
            indent_guides=False,
            padding=(0, 4),
        )
        console.print(syntax)

    # ── Additional notes ───────────────────────────────────────────────────────
    notes = issue.get("notes", "")
    if notes:
        console.print()
        console.print(f"  [dim]Note  [/dim][dim white]{notes}[/dim white]")

    console.print()
    console.print(Rule(style="dim white"))
    console.print()


def _render_footer(patch_data: dict) -> None:
    """Closing remark / next-step nudge."""
    footer = patch_data.get("next_steps", "")
    if not footer:
        return
    console.print(
        Panel(
            Text.assemble(
                ("  Next steps\n", "dim white"),
                (f"  {footer}", "white"),
            ),
            border_style="dim white",
            padding=(0, 1),
        )
    )
    console.print()


def _detect_lang(code: str) -> str:
    """Heuristic language detection for syntax highlighting."""
    stripped = code.strip()
    if stripped.startswith("<?php"):
        return "php"
    if stripped.startswith("#!") and "python" in stripped:
        return "python"
    if any(kw in stripped for kw in ["def ", "import ", "print(", "class "]):
        return "python"
    if any(kw in stripped for kw in ["function ", "const ", "let ", "var ", "=>"]):
        return "javascript"
    if any(kw in stripped for kw in ["<", "/>", 'Content-Security-Policy']):
        return "html"
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    if any(kw in stripped for kw in ["server {", "location /", "proxy_pass"]):
        return "nginx"
    return "text"
