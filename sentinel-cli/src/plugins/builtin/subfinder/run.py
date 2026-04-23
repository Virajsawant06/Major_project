"""
subfinder plugin — Sentinel Security Scanner
Subdomain enumeration using Project Discovery's subfinder.
Requires: subfinder binary in PATH (https://github.com/projectdiscovery/subfinder)

Install:
  go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
  OR: scoop install subfinder (Windows) / brew install subfinder (macOS)
"""

import json
import shutil
import subprocess
import tempfile
import os
from urllib.parse import urlparse


def _check_subfinder() -> tuple[bool, str]:
    path = shutil.which("subfinder")
    if path:
        return True, path
    candidates = [
        os.path.expanduser("~/go/bin/subfinder"),
        "/usr/local/bin/subfinder",
        r"C:\tools\subfinder.exe",
        r"C:\ProgramData\chocolatey\bin\subfinder.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return True, c
    return False, (
        "subfinder binary not found. Install:\n"
        "  go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest\n"
        "  OR: scoop install subfinder"
    )


def run(url: str, console=None, config: dict = None) -> list[dict]:
    """
    Enumerate subdomains for the target domain.
    Returns each found subdomain as an Informational finding.
    """
    available, subfinder_bin = _check_subfinder()
    if not available:
        return [{
            "id":          "subfinder-err-001",
            "tool":        "subfinder",
            "vuln_type":   "Subfinder Not Installed",
            "severity":    "Informational",
            "endpoint":    url,
            "parameter":   "",
            "description": subfinder_bin,
            "solution":    "Install subfinder binary and ensure it is in PATH.",
            "evidence":    "",
            "cweid":       "",
        }]

    parsed = urlparse(url)
    domain = parsed.hostname or url

    findings = []

    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tf:
            out_file = tf.name

        cmd = [
            subfinder_bin,
            "-d", domain,
            "-o", out_file,
            "-silent",
            "-timeout", "30",
        ]

        subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if os.path.exists(out_file):
            with open(out_file, "r", encoding="utf-8") as f:
                subdomains = [line.strip() for line in f if line.strip()]

            # Report each subdomain as an informational finding
            for i, sub in enumerate(subdomains):
                findings.append({
                    "id":          f"subfinder-{i+1:04d}",
                    "tool":        "subfinder",
                    "vuln_type":   "Subdomain Discovered",
                    "severity":    "Informational",
                    "endpoint":    f"http://{sub}",
                    "parameter":   "",
                    "description": f"Subdomain '{sub}' discovered for domain '{domain}'. Each subdomain is an additional attack surface.",
                    "solution":    "Review this subdomain — ensure it is intentional and not exposing sensitive services.",
                    "evidence":    sub,
                    "cweid":       "200",
                })

            if subdomains:
                # Add a summary finding
                findings.insert(0, {
                    "id":          "subfinder-summary",
                    "tool":        "subfinder",
                    "vuln_type":   f"Subdomain Enumeration — {len(subdomains)} found",
                    "severity":    "Low" if len(subdomains) > 5 else "Informational",
                    "endpoint":    url,
                    "parameter":   "",
                    "description": (
                        f"Subfinder discovered {len(subdomains)} subdomains for '{domain}'. "
                        "A large subdomain count increases the attack surface."
                    ),
                    "solution":    "Audit each subdomain. Remove unused or deprecated subdomains from DNS.",
                    "evidence":    ", ".join(subdomains[:10]) + ("..." if len(subdomains) > 10 else ""),
                    "cweid":       "200",
                })

    except subprocess.TimeoutExpired:
        findings.append({
            "id":          "subfinder-timeout",
            "tool":        "subfinder",
            "vuln_type":   "Subfinder Timeout",
            "severity":    "Informational",
            "endpoint":    url,
            "parameter":   "",
            "description": "Subfinder scan timed out after 120 seconds.",
            "solution":    "Try again with a longer timeout.",
            "evidence":    "",
            "cweid":       "",
        })
    except Exception as e:
        findings.append({
            "id":          "subfinder-err",
            "tool":        "subfinder",
            "vuln_type":   "Subfinder Error",
            "severity":    "Informational",
            "endpoint":    url,
            "parameter":   "",
            "description": str(e),
            "solution":    "Check subfinder installation.",
            "evidence":    "",
            "cweid":       "",
        })
    finally:
        if "out_file" in locals() and os.path.exists(out_file):
            os.unlink(out_file)

    return findings
