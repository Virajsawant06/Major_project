# Sentinel Security — NPM Installation Guide

> **AI-Powered Ethical Hacking & Patch Engine**  
> `sentinel-security@0.2.0` — Production Ready

---

## Prerequisites

Before installing, make sure you have the following on your system:

| Requirement | Version | Check Command |
|---|---|---|
| **Node.js** | v16 or higher | `node --version` |
| **npm** | v8 or higher | `npm --version` |
| **Python** | v3.9 or higher | `python --version` |
| **pip** | Latest | `pip --version` |

---

## Installation

### Step 1 — Install globally via npm

```bash
npm install -g sentinel-security
```

This will:
- Download the Sentinel CLI package
- Automatically create a Python virtual environment at `~/.sentinel/venv`
- Install all required Python dependencies inside that environment

> ⏱️ This may take 1–3 minutes on first install.

---

### Step 2 — Set your OpenRouter API Key

Sentinel uses [OpenRouter](https://openrouter.ai) to power its AI analysis, patch generation, and chat features.

**Get your free API Key at:** https://openrouter.ai/keys

Once you have it, set it as an environment variable:

#### Windows (PowerShell)
```powershell
$env:OPENROUTER_API_KEY="sk-or-your-key-here"
```

#### Windows (CMD)
```cmd
set OPENROUTER_API_KEY=sk-or-your-key-here
```

#### macOS / Linux
```bash
export OPENROUTER_API_KEY="sk-or-your-key-here"
```

#### Make it permanent (recommended)

**Windows**: Add it to System Environment Variables via Control Panel → System → Advanced → Environment Variables.

**macOS / Linux**: Add the `export` line to your `~/.bashrc` or `~/.zshrc` file:
```bash
echo 'export OPENROUTER_API_KEY="sk-or-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

---

### Step 3 — Verify the installation

Open a **new terminal window** and run:

```bash
sentinel
```

You should see the Sentinel banner:

```
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ...
  Ethical Hacking + AI Patch Engine   v0.2.0 — Production Ready
```

---

## Quick Start

### Run your first scan

```bash
sentinel scan --url https://example.com
```

### Generate AI patches for your last scan

```bash
sentinel patches
```

### Chat with AI about your scan results

```bash
sentinel chat
```

### Compare two scans to track progress

```bash
sentinel compare <scan-id-1> <scan-id-2>
```

### View scan history

```bash
sentinel history
```

### Run system health check

```bash
sentinel doctor
```

---

## Scan Modes

| Mode | Speed | Description |
|---|---|---|
| `--mode fast` | ~60–90 sec | Native engine only (recommended) |
| `--mode deep` | ~10 min max | Native + ZAP + Nikto (requires Java) |

**Example:**
```bash
sentinel scan --url https://example.com --mode fast
```

---

## Troubleshooting

### ❌ `sentinel: command not found`

You installed without the `-g` flag. Fix it:
```bash
npm install -g sentinel-security
```
Then close and reopen your terminal.

---

### ❌ `No module named 'bs4'` or other Python module errors

The Python virtual environment is missing a dependency. Run:

```bash
# Windows
~\.sentinel\venv\Scripts\pip.exe install beautifulsoup4 openai prompt_toolkit

# macOS / Linux
~/.sentinel/venv/bin/pip install beautifulsoup4 openai prompt_toolkit
```

Or force a full reinstall:
```bash
npm uninstall -g sentinel-security
Remove-Item -Recurse -Force ~/.sentinel/venv   # Windows PowerShell
npm install -g sentinel-security
```

---

### ❌ `Error: Python virtual environment not found`

Python was not found during installation. Ensure Python is installed and available in your PATH:
```bash
python --version   # Should print Python 3.9+
```

If Python is installed but not found, reinstall with:
```bash
npm install -g sentinel-security
```

---

### ❌ `Error generating patches: 429`

The AI model is temporarily rate-limited. This is normal for free models. Wait 30 seconds and try again:
```bash
sentinel patches
```

---

### ❌ `Missing OPENROUTER_API_KEY`

You haven't set your API key. Follow **Step 2** above. Then run:
```bash
sentinel doctor
```
This will show you which components are configured correctly.

---

### ❌ `sentinel` shows old version after update

Uninstall and reinstall:
```bash
npm uninstall -g sentinel-security
npm install -g sentinel-security
```

---

## Advanced Configuration

Sentinel stores all configuration and scan data in `~/.sentinel/`:

```
~/.sentinel/
├── config.json       # Your saved settings
├── scans/            # All scan reports (JSON)
│   └── 2026-04-23_13-14-15_example.com/
│       ├── findings.json
│       └── meta.json
├── venv/             # Python virtual environment
└── logs/
    └── sentinel.log  # Debug logs
```

### View your current settings
```bash
sentinel config show
```

### Change a setting
```bash
sentinel config set scan_mode fast
sentinel config set openrouter_model nvidia/nemotron-nano-9b-v2:free
```

---

## System Requirements

| Component | Required | Purpose |
|---|---|---|
| Python 3.9+ | ✅ Required | Core engine |
| OpenRouter API Key | ✅ Required | AI analysis & patches |
| Java 11+ | ⚠️ Optional | ZAP deep scan mode only |
| Docker | ⚠️ Optional | Nikto scanner |
| Nuclei / Subfinder | ⚠️ Optional | Advanced plugin scans |

---

## Get Help

- **Health Check**: `sentinel doctor`
- **Available Commands**: `sentinel --help`
- **In-shell Help**: Type `help` inside the Sentinel interactive shell
- **GitHub Issues**: https://github.com/your-repo/sentinel-cli/issues

---

*Sentinel Security is an ethical hacking tool. Only scan targets you own or have explicit written permission to test. Unauthorized scanning is illegal.*
