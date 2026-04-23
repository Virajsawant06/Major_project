"""
Sentinel Brain — AI Hacker Orchestrator

The AI is the brain. src/attack/ modules are its hands.

What the user sees:
  - Which phase is running
  - Which tool the brain called
  - How many findings each tool returned
  - The final hacker analysis

What the user does NOT see:
  - The AI's internal reasoning text
  - Every path the exposure check tries
  - Repeated errors
  - Raw Rich markup tags
"""

import os
import json
import warnings
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from src.intelligence.models import SUMMARY_MODEL

# Suppress urllib3/requests SSL warnings that flood the terminal
warnings.filterwarnings("ignore")

from src.attack.zap_scanner import run_zap_scan_live
from src.attack.nikto_scanner import run_nikto
from src.attack.exposure import check_exposure
from src.attack.auth_scanner import run_auth_scan
from src.attack.idor_scanner import run_idor_scan
from src.utils.cleaner import build_clean_report

load_dotenv()

# ── System prompt ──────────────────────────────────────────────────────────────

HACKER_PROMPT = """
You are Sentinel Brain — an elite penetration testing AI with explicit written
authorization to test the target provided.

You think exactly like an experienced attacker. Your methodology:

PHASE 1 — FAST RECON (ALWAYS RUN THESE)
1. Call run_exposure_check to find sensitive files and JS routes.
2. Call run_param_extract to crawl for forms and query parameters.
3. Call run_ssl_check to verify certificate security.

PHASE 2 — NATIVE ATTACK ENGINE (ALWAYS RUN THIS)
4. Call run_native_engine. This is your primary weapon. It uses the parameters found in Phase 1 to test for XSS, CSRF, SQLi, SSRF, and checks headers, cookies, etc.

PHASE 3 — DEEP SCAN TOOLS (ONLY IF AVAILABLE)
If the user requested a deep scan, you will have additional tools available (run_zap_scan, run_nikto_scan, run_auth_scan, run_idor_scan). Use them.
If they are not in your tools list, DO NOT try to call them.

WHEN DONE: Write a clear attack summary in plain English.
Be specific. Be honest about severity. Do not hype low-risk findings.
"""

# ── Tool schemas ───────────────────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "run_exposure_check",
            "description": "Checks for exposed sensitive files and mines JS bundles for API routes. Fast — always run first.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_param_extract",
            "description": "Crawls the target to discover forms and query parameters to feed to the native engine.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_ssl_check",
            "description": "Checks SSL/TLS certificate security.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_native_engine",
            "description": "Primary attack engine. Tests 11 vulnerability categories in parallel including XSS, SQLi, SSRF, CORS, Headers. Uses params found by param_extract.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_zap_scan",
            "description": "Full OWASP ZAP spider + active scan. Heavy weapon — use after native engine.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_nikto_scan",
            "description": "Nikto web server scanner. Finds outdated software and misconfigurations. Requires Docker.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_auth_scan",
            "description": "Checks default credentials, auth SQL injection, and token weaknesses.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_idor_scan",
            "description": "Checks for IDOR (parameter tampering) and access control flaws.",
            "parameters": {"type": "object", "properties": {"target_url": {"type": "string"}}, "required": ["target_url"]}
        }
    }
]

# ── Tool labels shown to the user ──────────────────────────────────────────────

TOOL_LABELS = {
    "run_exposure_check": "Exposure check   (sensitive files, API routes)",
    "run_param_extract":  "Parameter crawl  (forms, API endpoints)",
    "run_ssl_check":      "SSL/TLS check    (certificate health)",
    "run_native_engine":  "Native attack    (11 vulnerability checks)",
    "run_zap_scan":       "ZAP active scan  (deep spider, SQLi, injections)",
    "run_nikto_scan":     "Nikto scan       (server misconfigurations)",
    "run_auth_scan":      "Auth scan        (SQLi, Default Creds)",
    "run_idor_scan":      "IDOR scan        (Parameter Tampering)",
}

# ── Tool execution ─────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, target_url: str, auth_header: str = None, login_url: str = None, request_file: str = None, context: dict = None) -> list:
    """
    Runs the tool silently. No internal print output reaches the user.
    Returns a list of findings. Never raises.
    """
    if context is None:
        context = {}
        
    try:
        if tool_name == "run_exposure_check":
            return check_exposure(target_url, console=None)
            
        elif tool_name == "run_param_extract":
            from src.attack.param_extractor import ParamExtractor
            extractor = ParamExtractor(target_url)
            res = extractor.extract()
            context["get_params"] = res.get("get_params", [])
            context["forms"] = res.get("forms", [])
            return [{"info": f"Extracted {len(context['get_params'])} params and {len(context['forms'])} forms"}]
            
        elif tool_name == "run_native_engine":
            from src.attack.native_engine import SentinelNativeEngine
            engine = SentinelNativeEngine(target_url)
            return engine.run_all(context.get("get_params", []), context.get("forms", []))
            
        elif tool_name == "run_ssl_check":
            from src.plugins.builtin import ssl_check
            # SSL check plugin is a module with a run() function, but wait, it's run.py in plugins/builtin/ssl-check/
            # Better to use the plugin manager
            from src.plugins.manager import run_plugin
            return run_plugin("ssl-check", target_url, console=None)

        elif tool_name == "run_zap_scan":
            results = run_zap_scan_live(target_url)
            return results.get("findings", [])

        elif tool_name == "run_nikto_scan":
            return run_nikto(target_url, console=None)

        elif tool_name == "run_auth_scan":
            return run_auth_scan(target_url, login_url=login_url, request_file=request_file, console=None)

        elif tool_name == "run_idor_scan":
            return run_idor_scan(target_url, auth_header=auth_header, request_file=request_file, console=None)

        else:
            return [{"error": f"Unknown tool: {tool_name}"}]

    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "10061" in error_msg or "10060" in error_msg:
            hint = "ZAP is not running — start it first with: sentinel start"
        elif "Cannot connect" in error_msg:
            hint = "ZAP is not running — start it first with: sentinel start"
        else:
            # Keep error short — don't flood with stack traces
            hint = error_msg.split("\n")[0][:120]
        return [{"error": hint, "tool": tool_name, "severity": "Info"}]


# ── The brain ──────────────────────────────────────────────────────────────────

class AttackBrain:
    """
    OpenRouter-powered hacker orchestrator.

    Usage:
        brain = AttackBrain()
        report = brain.attack("https://target.com", console=console)

    Returns the same report dict format as run_zap_scan_live.
    """

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set.\n"
                "Set OPENROUTER_API_KEY in .env"
            )
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

    def attack(self, target_url: str, mode: str = "deep", console=None, auth_header=None, login_url=None, request_file=None) -> dict:
        """
        AI-orchestrated attack loop. Clean terminal output only.
        AI reasons internally — user sees phase + finding counts only.
        """
        from rich.console import Console
        from rich.rule import Rule

        # Use provided console or create one — ensures Rich markup renders
        con = console if console else Console()

        con.print(f"\n[bold cyan]  Sentinel Brain[/bold cyan]  [dim]target: {target_url} | mode: {mode}[/dim]")
        con.print(Rule(style="dim cyan"))
        
        # Filter available tools based on mode
        available_tools = []
        for schema in TOOL_SCHEMAS:
            name = schema["function"]["name"]
            if mode == "fast" and name in ["run_zap_scan", "run_nikto_scan", "run_auth_scan", "run_idor_scan"]:
                continue
            available_tools.append(schema)

        messages = [
            {"role": "system", "content": HACKER_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Target: {target_url}\n"
                    f"Mode: {mode}\n"
                    "Authorization granted. Begin penetration test."
                )
            }
        ]

        all_findings = []
        tools_used = set()
        errors_seen = set()   # deduplicate repeated error messages
        MAX_STEPS = 10

        # ── Intelligence loop ──────────────────────────────────────────────────
        scan_context = {}
        for step in range(MAX_STEPS):

            response = self.client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b:free",
                messages=messages,
                tools=available_tools,
                tool_choice="auto",
                temperature=0.2,
                max_completion_tokens=1024
            )

            msg = response.choices[0].message
            messages.append(msg)

            # AI's reasoning is intentionally hidden from user
            # It goes into messages for context but not to terminal

            if not msg.tool_calls:
                break

            for call in msg.tool_calls:
                tool_name = call.function.name
                args = json.loads(call.function.arguments)
                url = args.get("target_url", target_url)

                # Skip duplicate tool calls silently
                if tool_name in tools_used:
                    messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps({"note": "Already ran."})
                    })
                    continue

                tools_used.add(tool_name)
                label = TOOL_LABELS.get(tool_name, tool_name)
                con.print(f"\n  [cyan]▸[/cyan] {label}")

                findings = execute_tool(tool_name, url, auth_header=auth_header, login_url=login_url, request_file=request_file, context=scan_context)

                # Separate real findings from errors
                valid   = [f for f in findings if "error" not in f]
                errors  = [f for f in findings if "error" in f]

                all_findings.extend(valid)

                # Show clean finding count
                if valid:
                    con.print(f"    [green]✓[/green] {len(valid)} finding(s)")
                else:
                    con.print(f"    [dim]✓ Complete — no findings[/dim]")

                # Show errors once only, deduplicated, short
                for err in errors:
                    msg_text = err.get("error", "")
                    if msg_text and msg_text not in errors_seen:
                        errors_seen.add(msg_text)
                        con.print(f"    [yellow]![/yellow] {msg_text}")

                # Feed result back to AI (truncate if huge)
                result_str = json.dumps({
                    "findings_count": len(valid),
                    "findings": valid
                })
                if len(result_str) > 12000:
                    result_str = result_str[:12000] + "... [TRUNCATED]"

                messages.append({
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": result_str,
                })

        con.print()
        con.print(Rule(style="dim cyan"))

        # ── Final hacker analysis ──────────────────────────────────────────────
        analysis = self._get_analysis(messages, all_findings, target_url)
        if analysis:
            from rich.panel import Panel
            con.print(Panel(
                analysis,
                title="[bold red]Hacker Analysis[/bold red]",
                border_style="red",
                padding=(1, 2)
            ))

        # ── Build report ───────────────────────────────────────────────────────
        raw = {
            "scan_id":        f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_url":     target_url,
            "scanned_at":     datetime.now().isoformat(),
            "tool":           f"Sentinel Brain (OpenRouter + {', '.join(sorted(tools_used))})",
            "total_findings": len(all_findings),
            "findings":       all_findings,
            "attack_summary": analysis,
        }

        return build_clean_report(raw)

    def _get_analysis(self, messages: list, findings: list, target_url: str) -> str:
        """Silent AI call for the final plain-English summary."""
        if not findings:
            return "No significant findings on this target."

        try:
            summary_messages = messages + [{
                "role": "user",
                "content": (
                    f"Test complete on {target_url}. {len(findings)} findings.\n\n"
                    "Write the final attack summary (max 150 words):\n"
                    "1. Most dangerous finding and why\n"
                    "2. What a real attacker would DO with these findings\n"
                    "3. Which findings chain together\n"
                    "4. Single top priority fix\n\n"
                    "Direct language. No corporate speak."
                )
            }]

            resp = self.client.chat.completions.create(
                model=SUMMARY_MODEL,
                messages=summary_messages,
                temperature=0.3,
                max_completion_tokens=300
            )
            return resp.choices[0].message.content

        except Exception as e:
            return f"Analysis unavailable: {e}"