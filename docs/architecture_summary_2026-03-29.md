# 🛡️ Sentinel AI CLI: Project Overview & Architecture

**Date:** 2026-03-29

## Project Overview
**Sentinel** is an automated, AI-orchestrated penetration testing pipeline. Instead of just running standard security scanners blindly, it uses an LLM (Groq AI with the `llama-3.3-70b-versatile` model) acting as the "Brain" to orchestrate the attack intelligently. The AI decides which tools to run, prioritizes fast reconnaissance (like exposure checks), chains findings together, and ultimately produces a clean, severity-ranked report avoiding duplicate or noisy findings.

## 🗂️ Core Architecture & File Purposes

### 1. Entry Points & CLI Output (`src/main.py` & `src/cli/app.py`)
- **`src/main.py`**: The primary entry point for the tool. It handles the `rich` UI rendering for the terminal (progress bars, styled tables, colors), extracts the target `--url`, and strictly enforces an ethics disclaimer. It delegates the actual scan to the `AttackBrain` and writes the final output to a JSON file in the `output/` folder.
- **`src/cli/app.py`**: Contains similar functionality to `main.py` but currently acts as a traditional scanner that calls ZAP directly instead of routing through the AI Brain.

### 2. The AI Orchestrator (`src/intelligence/brain.py`)
- **`AttackBrain` Class**: This is the core logic. It sends a system prompt to Groq defining the tool as an elite penetration tester. The LLM operates in a loop up to 10 times, dynamically calling python functions as tools:
  - `run_exposure_check` (forced as phase 1)
  - `run_zap_scan`
  - `run_nikto_scan`
- Once it finishes collecting results from these "hands", the Brain analyzes the full list of findings to produce a plain-English attack summary (e.g., explaining the most dangerous vulnerability, how a real attacker would chain them, and prioritizing fixes).

### 3. The Attack Modules (`src/attack/`)
These are the physical tools executed by the AI Brain.
- **`zap_scanner.py`**: Interacts with a locally running OWASP ZAP instance via its REST API (`http://127.0.0.1:8080`). It dynamically seeds URLs, triggers the spider, parses passive results, runs active scans, and retrieves all vulnerability alerts.
- **`exposure.py`**: Fast reconnaissance custom script that looks for exposed sensitive files (`.env`, `.git`, swagger documentation, actuator endpoints, etc.).
- **`nikto_scanner.py`**: A wrapper to trigger Nikto, checking for outdated software and server misconfigurations.

### 4. Utilities & Reports (`src/utils/cleaner.py` & `src/output/`)
- **`cleaner.py`**: Used across the attack modules to sanitize, deduplicate, and organize the raw vulnerability dictionaries retrieved from the different tools.
- **`output/`**: The directory where all completed scans (JSON reports) are saved for historic logging and review.

Sentinel integrates the exhaustive scanning capabilities of standard tools (ZAP and Nikto) with the reasoning engine of an LLM to deliver context-aware hacker insights automatically.
