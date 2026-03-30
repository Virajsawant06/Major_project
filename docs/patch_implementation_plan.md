# Sentinel CLI & Patch Engine Implementation

This plan details the transformation of Sentinel into a modern, interactive CLI tool (like `claude`) and the addition of the new AI-powered Patch Engine.

## Proposed Changes

### 1. Global CLI Entry Point (`setup.py` & `sentinel_cli.py`)
To make `sentinel` a global command in your PowerShell:
- **[MODIFY] `setup.py`**: Ensure the package installs an executable entry point `sentinel`.
- **[MODIFY] `sentinel_cli.py`**: Build a `typer` or `cmd`-based application that natively processes:
  - `sentinel` (no args): Drops you into an interactive REPL shell displaying the ASCII art and waiting for commands.
  - `sentinel scan <url>`: Replaces `start.bat`, running your target directly.
  - `sentinel patches <output_file>`: Invokes the new Patch engine.

### 2. The Patch Engine (`src/patch/engine.py`)
- **[NEW] `src/patch/engine.py`**: A new module dedicated entirely to remediation.
- It will read the `.json` output from your attack scans.
- It will parse the findings, group them by severity/category, and send them to Groq using a highly specific prompt.
- **Groq Prompting**: The prompt will strictly instruct Groq to return JSON containing:
  - Grouped vulnerability data
  - "Does it affect you right now?" context.
  - "Paste this fix" exact code snippets.
  - Estimated fix times (e.g., "Fix in 30 min").

### 3. Rich CLI UI (`src/cli/ui.py`)
To exactly match the sleek interface from your screenshot:
- **[NEW] `src/cli/ui.py`**: A rendering module using `rich`.
  - **Stat Bar**: Renders the High (Green/Red), Medium (Orange), Low (Blue), and Total boxes cleanly at the top.
  - **Summary**: "Bottom line: Your app is NOT broken into..."
  - **Patch Cards**: Renders the `"WHAT TO FIX"` cards. Utilizing `rich.panel.Panel` to create the red headers (`* Your XSS defence is switched off - MEDIUM`), white body text, and green code blocks.

### 4. Interactive Shell (`src/cli/repl.py`)
- **[NEW] `src/cli/repl.py`**: If a user just types `sentinel`, they get the beautiful ASCII art, and a `Sentinel >` prompt. They can type `scan http://target` or `patches output/scan_123.json` inside this eternal loop.

## User Review Required

**ZAP Daemon Handling**: Your `start.bat` currently takes 40 seconds to boot ZAP before running Python. 
When we move to `sentinel scan` or the interactive menu, do you want Python to silently invoke that ZAP process in the background? Or do you want to keep using your `start.bat` strictly to boot ZAP and open the `sentinel` Python shell?
