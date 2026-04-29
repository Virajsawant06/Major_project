# Sentinel CLI Codebase Architecture & File Explanations

This document provides a comprehensive overview of the Sentinel CLI codebase, located in the `sentinel-cli/src` directory. The project is organized logically into modules representing different functional domains (UI, AI Intelligence, Attack Engines, and Patching).

## Core Entry Point

### `src/main.py`
The main entry point for the Sentinel CLI application. It uses the `Typer` library for command parsing and `Rich` for rendering a beautiful terminal UI. It defines the core commands (like `scan`, `patches`, `chat`, `compare`, `history`, and `doctor`) and routes them to the appropriate underlying modules.

---

## 1. CLI & UI (`src/cli/`)
Handles the interactive user interface, shell loops, and terminal output formatting.

*   **`src/cli/app.py`**: Contains helper functions for rendering scan summaries and finding details in the terminal using `Rich` components (tables, panels, and text formatting).
*   **`src/cli/repl.py` & `src/cli/shell.py`**: Implement the interactive REPL (Read-Eval-Print Loop) shell for the CLI, allowing users to enter a persistent interactive mode instead of running single one-off commands.

---

## 2. Attack Engines (`src/attack/`)
These files contain the actual scanning and enumeration tools that the AI "Brain" calls to find vulnerabilities.

*   **`src/attack/native_engine.py`**: The pure-Python, extremely fast vulnerability scanning engine. It natively checks for issues like XSS, SQLi, SSRF, CORS, missing security headers, and CSRF without relying on external binaries.
*   **`src/attack/zap_scanner.py`**: Integrates with the OWASP ZAP daemon. It triggers deep spiders and active scans via the ZAP API.
*   **`src/attack/nikto_scanner.py`**: A wrapper for running the Nikto web server scanner (often via Docker) to find server misconfigurations.
*   **`src/attack/auth_scanner.py`**: Specifically targets authentication flows, checking for default credentials, auth-related SQL injections, and weak tokens.
*   **`src/attack/idor_scanner.py`**: Scans for Insecure Direct Object References (IDOR) by tampering with parameters.
*   **`src/attack/exposure.py`**: Runs "Fast Recon" to find exposed sensitive files (e.g., `.env`, `.git`) and mines JavaScript bundles for hidden API routes.
*   **`src/attack/param_extractor.py`**: Crawls the target URL specifically to extract GET query parameters and POST forms. These parameters are then fed into the `native_engine` for testing.

---

## 3. Artificial Intelligence (`src/intelligence/`)
The "Brain" of the operation. Orchestrates attack tools and interprets the findings.

*   **`src/intelligence/brain.py`**: The primary AI orchestrator (using OpenRouter). It receives a target, reasons about which tools to use (from the `src/attack/` directory), executes them, and writes a final human-readable hacker summary of the findings.
*   **`src/intelligence/ollama_brain.py`**: A localized version of the AI orchestrator that uses local LLMs via Ollama, allowing for offline, privacy-preserving scans.
*   **`src/intelligence/chat_engine.py`**: Powers the interactive `sentinel chat` command, allowing users to have an interactive Q&A session with the AI regarding their specific scan results.
*   **`src/intelligence/compare_engine.py`**: Compares two different scan reports to track progress, identifying new, fixed, or recurring vulnerabilities.
*   **`src/intelligence/models.py`**: Configuration constants defining which AI models to use for different tasks (e.g., scanning, summarizing, chatting).

---

## 4. Remediation & Patching (`src/patch/`)
Handles the generation of secure code fixes for discovered vulnerabilities.

*   **`src/patch/engine.py`**: Parses the `findings.json` from a scan and feeds the vulnerabilities into an LLM to generate syntactically correct and secure code patches.
*   **`src/patch/ui.py`**: Renders the generated code patches in a beautiful, readable format within the terminal (using syntax highlighting and diff views).

---

## 5. Configuration & Plugins (`src/config/` & `src/plugins/`)
Manages system settings and extensible third-party tools.

*   **`src/config/manager.py`**: Handles loading and saving user preferences, API keys, and managing the local directory structure for scan history and outputs.
*   **`src/plugins/manager.py`**: The plugin loader. It registers and executes external tools or custom scripts.
*   **`src/plugins/builtin/*/run.py`**: The actual plugin scripts for built-in tools such as:
    *   **`nuclei`**: Fast vulnerability scanner.
    *   **`subfinder`**: Subdomain enumeration.
    *   **`headers-check`**: Security header validation.
    *   **`ssl-check`**: TLS/SSL certificate health.

---

## 6. Utilities (`src/utils/`)
General helper scripts.

*   **`src/utils/cleaner.py`**: Sanitizes, formats, and structures the raw data from various tools into a unified JSON report format.
*   **`src/utils/replay.py`**: Utility to replay or manually re-trigger specific raw HTTP requests for verification.
