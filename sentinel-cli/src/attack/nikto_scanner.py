import subprocess
import json


def run_nikto(target_url, console=None):
    """
    Run Nikto via Docker.

    console=None → completely silent (used by brain.py)
    console=<Console> → prints progress to terminal (used by direct CLI calls)
    """

    def log(msg):
        # Only print if a console was explicitly provided
        if console:
            console.print(msg)

    log("[yellow][*] Running Nikto — server misconfiguration scan...[/yellow]")

    try:
        result = subprocess.run([
            "docker", "run", "--rm",
            "frapsoft/nikto",
            "-h", target_url,
            "-Format", "json",
            "-nointeractive",
            "-timeout", "10",
        ], capture_output=True, text=True, timeout=120)

        findings = []
        for line in result.stdout.splitlines():
            try:
                item = json.loads(line)
                if item.get("id"):
                    findings.append({
                        "tool":        "nikto",
                        "vuln_type":   item.get("msg", "Unknown"),
                        "severity":    "Medium",
                        "endpoint":    target_url + item.get("url", ""),
                        "method":      "GET",
                        "evidence":    item.get("msg", ""),
                        "description": item.get("msg", ""),
                    })
            except Exception:
                continue

        log(f"[green][+] Nikto complete — {len(findings)} findings[/green]")
        return findings

    except subprocess.TimeoutExpired:
        log("[yellow][!] Nikto timed out — skipping[/yellow]")
        return []
    except Exception as e:
        log(f"[red][!] Nikto failed: {e}[/red]")
        return []