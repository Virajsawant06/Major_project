"""
nuclei plugin — Sentinel Security Scanner
Runs Project Discovery Nuclei against the target with community templates.
Requires: nuclei binary in PATH (https://github.com/projectdiscovery/nuclei)

Install nuclei:
  Linux/macOS: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
  Windows:     scoop install nuclei   OR   choco install nuclei
  Docker:      docker pull projectdiscovery/nuclei
"""

import json
import shutil
import subprocess
import tempfile
import os
from pathlib import Path


SEVERITY_MAP = {
    "critical": "High",
    "high":     "High",
    "medium":   "Medium",
    "low":      "Low",
    "info":     "Informational",
    "unknown":  "Informational",
}


def _check_nuclei() -> tuple[bool, str]:
    """Return (available, path_or_error)."""
    path = shutil.which("nuclei")
    if path:
        return True, path
    # Try common locations
    candidates = [
        os.path.expanduser("~/go/bin/nuclei"),
        "/usr/local/bin/nuclei",
        r"C:\tools\nuclei.exe",
        r"C:\ProgramData\chocolatey\bin\nuclei.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return True, c
    return False, (
        "nuclei binary not found. Install it:\n"
        "  Linux/macOS: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest\n"
        "  Windows:     scoop install nuclei\n"
        "  Docker:      docker pull projectdiscovery/nuclei"
    )


def run(url: str, console=None, config: dict = None) -> list[dict]:
    """
    Execute nuclei against the target URL and return parsed findings.
    """
    available, nuclei_bin = _check_nuclei()
    if not available:
        return [{
            "id":          "nuclei-err-001",
            "tool":        "nuclei",
            "vuln_type":   "Nuclei Not Installed",
            "severity":    "Informational",
            "endpoint":    url,
            "parameter":   "",
            "description": nuclei_bin,
            "solution":    "Install nuclei binary and ensure it is in PATH.",
            "evidence":    "",
            "cweid":       "",
        }]

    findings = []

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tf:
        out_file = tf.name

    try:
        cmd = [
            nuclei_bin,
            "-u", url,
            "-json",
            "-o", out_file,
            "-severity", "critical,high,medium,low,info",
            "-silent",
            "-no-color",
            "-timeout", "30",
            "-bulk-size", "10",
            "-concurrency", "10",
        ]

        # Update templates silently first (best effort)
        try:
            subprocess.run(
                [nuclei_bin, "-update-templates", "-silent"],
                timeout=60, capture_output=True
            )
        except Exception:
            pass

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse JSONL output
        if os.path.exists(out_file):
            with open(out_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        info       = item.get("info", {})
                        severity   = SEVERITY_MAP.get(
                            info.get("severity", "info").lower(), "Informational"
                        )
                        template   = item.get("template-id", "unknown")
                        name       = info.get("name", template)
                        matched_at = item.get("matched-at", url)
                        desc       = info.get("description", "")
                        remediation= info.get("remediation", "Review the nuclei template documentation.")
                        refs       = info.get("reference", [])
                        if isinstance(refs, list):
                            refs = ", ".join(refs[:2])

                        findings.append({
                            "id":          f"nuclei-{i+1:04d}",
                            "tool":        "nuclei",
                            "vuln_type":   name,
                            "severity":    severity,
                            "endpoint":    matched_at,
                            "parameter":   item.get("matcher-name", ""),
                            "description": desc or f"Nuclei template '{template}' matched.",
                            "solution":    remediation,
                            "evidence":    item.get("extracted-results", [""])[0] if item.get("extracted-results") else item.get("curl-command", "")[:200],
                            "cweid":       "",
                            "references":  refs,
                        })
                    except (json.JSONDecodeError, KeyError):
                        continue

    except subprocess.TimeoutExpired:
        findings.append({
            "id":          "nuclei-timeout",
            "tool":        "nuclei",
            "vuln_type":   "Nuclei Scan Timeout",
            "severity":    "Informational",
            "endpoint":    url,
            "parameter":   "",
            "description": "Nuclei scan exceeded 5-minute timeout.",
            "solution":    "Try with a narrower template set: --severity high,critical",
            "evidence":    "",
            "cweid":       "",
        })
    except Exception as e:
        findings.append({
            "id":          "nuclei-err",
            "tool":        "nuclei",
            "vuln_type":   "Nuclei Error",
            "severity":    "Informational",
            "endpoint":    url,
            "parameter":   "",
            "description": str(e),
            "solution":    "Check nuclei installation and network connectivity.",
            "evidence":    "",
            "cweid":       "",
        })
    finally:
        if os.path.exists(out_file):
            os.unlink(out_file)

    return findings
