# Sentinel AI - Quick Start Guide

Welcome to the new interactive Sentinel AI Engine. This document outlines how to run and use the various components of the CLI.

> [!IMPORTANT]
> The central entry point for Sentinel is now **`sentinel.bat`**. 
> Run all commands outlined below from the `sentinel-cli` root folder inside PowerShell or Command Prompt.

---

## 1. Interactive Mode (`claude` style)

The interactive shell drops you into an immersive hacking workspace. It keeps your interface clean and allows you to string commands together dynamically.

**Command:**
```powershell
.\sentinel.bat
```

**What it does:**
1. Loads the Sentinel ASCII banner.
2. Presents the `Sentinel >` prompt.
3. Allows you to type `scan <url>` or `patches` directly into the terminal without reloading the script.
4. Type `help` inside the shell for a list of available actions.

---

## 2. Direct Scan Mode

If you just want to kick off a fully orchestrated attack against an application (and optionally provide traffic replays), you can bypass the interactive menu.

**Command:**
```powershell
.\sentinel.bat scan --url http://target.com
```

**What it does:**
1. **ZAP Daemon Boot**: Automatically launches the Zed Attack Proxy in the background (waits 40 seconds).
2. **Groq Orchestration**: The AI brain analyzes exposure routes, launches active injection phases, and decides if Authentication or IDOR modules are required based on discovered data.
3. Outputs a `.json` report file automatically to the `output/` directory.

### Advanced Scanning (Request Replay)
To eliminate guesswork, you can feed Sentinel your raw HTTP traffic (such as a Burp Suite intercept) allowing it to mutate JSON bodies, URLs, and Queries for IDOR vulnerabilities natively.

```powershell
.\sentinel.bat scan --url http://target.com --request-file capture.txt
```

---

## 3. The AI Patch Engine

Once you have completed a scan, Sentinel can ingest the findings and leverage Groq to act as a Senior AppSec Engineer, generating a highly structured, color-coded visual report showing you exactly how to fix the code.

**Auto-Select Latest Run:**
```powershell
.\sentinel.bat patches
```
*If you run this with no extra arguments, Sentinel automatically selects the most recent `.json` file from your `output/` directory and analyzes it.*

**Analyze a Specific Report:**
```powershell
.\sentinel.bat patches output/my_custom_scan_results.json
```

**What it does:**
1. Renders a colorful **Stat Bar** showing the total High/Medium/Low vulnerabilities at the top of your terminal.
2. Condenses the scan into a **Bottom Line** indicating if you are actively exploitable.
3. For each vulnerability, the UI prints:
   - **Severity Header**: E.g., `* XSS Defence is Switched Off - MEDIUM`
   - **Context Block**: Answers *"Does it affect you right now?"* based on Groq's analysis.
   - **Paste This Fix**: Provides the exact code snippet required to remediate the vulnerability instantly.
