"""
Sentinel Ollama Brain — Local AI Orchestrator
100% offline, privacy-preserving vulnerability analysis using a local Ollama model.

Usage:
    brain = OllamaBrain()
    report = brain.attack("https://target.com", console=console)

Requires: Ollama running at http://localhost:11434 (configurable via sentinel config set ollama_host)
Set model: sentinel ollama set-model llama3
"""

import json
import os
import requests
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

from src.attack.exposure import check_exposure
from src.attack.auth_scanner import run_auth_scan
from src.attack.idor_scanner import run_idor_scan
from src.utils.cleaner import build_clean_report
from src.config import manager as cfg


# ── System prompt for local model ─────────────────────────────────────────────
HACKER_PROMPT = """You are Sentinel — an elite penetration testing AI analyzing a web target.
Your task: decide which security checks to run, interpret results, and write a final threat analysis.

Available tools you can call (respond with JSON to invoke them):
- run_exposure_check: Find exposed .env, .git, swagger, API routes
- run_auth_scan: Test authentication (default creds, SQL auth bypass)
- run_idor_scan: Test IDOR and parameter tampering
- done: Finish and write analysis

Always start with run_exposure_check. Chain findings. Max 5 tool calls.

When invoking a tool, respond ONLY with:
{"tool": "<tool_name>", "reason": "<why you're running this>"}

When finished, respond ONLY with:
{"tool": "done", "analysis": "<your attack analysis in plain English, max 150 words>"}
"""


class OllamaBrain:
    """
    Local AI-powered security scanner using Ollama.
    Falls back gracefully if Ollama is not running.
    """

    def __init__(self):
        self.host  = cfg.get("ollama_host", "http://localhost:11434")
        self.model = cfg.get("ollama_model", "")
        if not self.model:
            raise ValueError(
                "No Ollama model set.\n"
                "Set one with: sentinel ollama set-model <model>\n"
                "List models:  sentinel ollama models"
            )

    def _is_available(self) -> bool:
        """Check if Ollama daemon is reachable."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[dict]:
        """Return available local models."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=10)
            r.raise_for_status()
            return r.json().get("models", [])
        except Exception as e:
            raise ConnectionError(f"Cannot reach Ollama at {self.host}: {e}")

    def _chat(self, messages: list[dict]) -> str:
        """Send a chat request to Ollama. Returns response text."""
        payload = {
            "model":    self.model,
            "messages": messages,
            "stream":   False,
            "options":  {
                "temperature": 0.2,
                "num_predict": 512,
            },
        }
        r = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=120,
        )
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")

    def _extract_json(self, text: str) -> dict | None:
        """Extract the first JSON object from LLM response text."""
        text = text.strip()
        # Find first {...}
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return None

    def _execute_tool(self, tool_name: str, target_url: str, auth_header: str = None, login_url: str = None) -> list[dict]:
        """Execute the named tool silently. Returns findings list."""
        try:
            if tool_name == "run_exposure_check":
                return check_exposure(target_url, console=None)
            elif tool_name == "run_auth_scan":
                return run_auth_scan(target_url, login_url=login_url, console=None)
            elif tool_name == "run_idor_scan":
                return run_idor_scan(target_url, auth_header=auth_header, console=None)
            else:
                return []
        except Exception as e:
            return [{"error": str(e)[:120], "tool": tool_name, "severity": "Informational"}]

    TOOL_LABELS = {
        "run_exposure_check": "Exposure check   (sensitive files, API routes)",
        "run_auth_scan":      "Auth scan        (default creds, SQL auth bypass)",
        "run_idor_scan":      "IDOR scan        (parameter tampering)",
    }

    def attack(
        self,
        target_url: str,
        console=None,
        auth_header: str = None,
        login_url: str   = None,
    ) -> dict:
        """
        Orchestrate a security scan using local Ollama AI.
        Returns report dict in the same format as AttackBrain.
        """
        from rich.console import Console
        from rich.rule import Rule
        from rich.panel import Panel

        con = console if console else Console()

        if not self._is_available():
            con.print(f"[red]✗ Ollama not running at {self.host}[/red]")
            con.print(f"[dim]Start Ollama: ollama serve[/dim]")
            return self._empty_report(target_url)

        con.print(f"\n[bold cyan]  Sentinel Ollama Brain[/bold cyan]  "
                  f"[dim]model: {self.model}  target: {target_url}[/dim]")
        con.print(Rule(style="dim cyan"))

        messages = [
            {"role": "system", "content": HACKER_PROMPT},
            {"role": "user",   "content": f"Target: {target_url}\nBegin penetration test. Start with exposure check."},
        ]

        all_findings  = []
        tools_used    = set()
        analysis_text = ""
        MAX_STEPS     = 8

        for step in range(MAX_STEPS):
            try:
                raw_response = self._chat(messages)
            except Exception as e:
                con.print(f"[red]  Ollama error: {e}[/red]")
                break

            decision = self._extract_json(raw_response)

            if not decision:
                # Model gave non-JSON — treat as final analysis
                analysis_text = raw_response.strip()
                break

            tool_name = decision.get("tool", "")

            if tool_name == "done":
                analysis_text = decision.get("analysis", "")
                break

            if tool_name not in self.TOOL_LABELS:
                # Unknown tool — stop
                break

            if tool_name in tools_used:
                messages.append({
                    "role":    "assistant",
                    "content": raw_response,
                })
                messages.append({
                    "role":    "user",
                    "content": json.dumps({"note": "Already ran this tool. Choose a different one or call done."}),
                })
                continue

            tools_used.add(tool_name)
            label = self.TOOL_LABELS[tool_name]
            con.print(f"\n  [cyan]▸[/cyan] {label}")

            findings = self._execute_tool(tool_name, target_url, auth_header, login_url)
            valid    = [f for f in findings if "error" not in f]
            errors   = [f for f in findings if "error" in f]

            all_findings.extend(valid)

            if valid:
                con.print(f"    [green]✓[/green] {len(valid)} finding(s)")
            else:
                con.print(f"    [dim]✓ Complete — no findings[/dim]")

            for err in errors:
                con.print(f"    [yellow]![/yellow] {err.get('error', '')}")

            # Feed results back
            result_str = json.dumps({"findings_count": len(valid), "findings": valid})
            if len(result_str) > 8000:
                result_str = result_str[:8000] + "... [TRUNCATED]"

            messages.append({"role": "assistant", "content": raw_response})
            messages.append({
                "role":    "user",
                "content": (
                    f"Tool results for {tool_name}:\n{result_str}\n\n"
                    "Decide what to do next. Call another tool or call done with your analysis."
                ),
            })

        con.print()
        con.print(Rule(style="dim cyan"))

        if analysis_text:
            con.print(Panel(
                analysis_text,
                title="[bold magenta]Ollama Analysis[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            ))

        raw = {
            "scan_id":        f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_url":     target_url,
            "scanned_at":     datetime.now().isoformat(),
            "tool":           f"Sentinel Ollama Brain ({self.model})",
            "total_findings": len(all_findings),
            "findings":       all_findings,
            "attack_summary": analysis_text,
        }

        return build_clean_report(raw)

    def _empty_report(self, target_url: str) -> dict:
        return build_clean_report({
            "scan_id":        f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_url":     target_url,
            "scanned_at":     datetime.now().isoformat(),
            "tool":           "Sentinel Ollama Brain (unavailable)",
            "total_findings": 0,
            "findings":       [],
            "attack_summary": "Ollama was not available. No scan performed.",
        })
