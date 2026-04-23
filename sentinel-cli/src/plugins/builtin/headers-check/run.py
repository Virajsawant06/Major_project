"""
headers-check plugin — Sentinel Security Scanner
Audits HTTP response headers for security best practices.
Checks: CSP, HSTS, X-Frame-Options, X-Content-Type-Options,
        Referrer-Policy, Permissions-Policy, CORS, Server disclosure.
"""

import requests
import warnings
warnings.filterwarnings("ignore")


# (header_name, severity, description, recommended_value, cwe_id)
SECURITY_HEADERS = [
    (
        "Content-Security-Policy",
        "High",
        "Content Security Policy (CSP) is not set. Attackers can inject malicious scripts (XSS).",
        "default-src 'self'; script-src 'self'; object-src 'none';",
        "693",
    ),
    (
        "Strict-Transport-Security",
        "Medium",
        "HSTS header missing. Browsers may downgrade HTTPS connections to HTTP.",
        "max-age=31536000; includeSubDomains; preload",
        "319",
    ),
    (
        "X-Frame-Options",
        "Medium",
        "X-Frame-Options missing. Page may be embedded in iframes (clickjacking).",
        "DENY or SAMEORIGIN",
        "1021",
    ),
    (
        "X-Content-Type-Options",
        "Low",
        "X-Content-Type-Options missing. Browser may MIME-sniff responses.",
        "nosniff",
        "693",
    ),
    (
        "Referrer-Policy",
        "Low",
        "Referrer-Policy not set. Full URL may be leaked in Referer headers.",
        "strict-origin-when-cross-origin",
        "116",
    ),
    (
        "Permissions-Policy",
        "Low",
        "Permissions-Policy (formerly Feature-Policy) not set. Browser features unrestricted.",
        "geolocation=(), microphone=(), camera=()",
        "693",
    ),
    (
        "X-XSS-Protection",
        "Low",
        "X-XSS-Protection header not set. Legacy browsers may not have XSS filter active.",
        "1; mode=block",
        "693",
    ),
    (
        "Cache-Control",
        "Low",
        "Cache-Control not set on response. Sensitive data may be cached.",
        "no-store, no-cache, must-revalidate",
        "524",
    ),
]

SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}


def run(url: str, console=None, config: dict = None) -> list[dict]:
    """
    Fetch the URL and audit response headers.
    Returns a list of finding dicts.
    """
    findings = []

    try:
        resp = requests.get(
            url,
            timeout=15,
            verify=False,
            allow_redirects=True,
            headers={"User-Agent": "Sentinel-SecurityScanner/1.0"},
        )
    except requests.exceptions.ConnectionError:
        return [{"tool": "headers-check", "vuln_type": "Connection Failed", "severity": "Informational",
                 "endpoint": url, "description": f"Could not connect to {url}", "parameter": ""}]
    except Exception as e:
        return [{"tool": "headers-check", "vuln_type": "Error", "severity": "Informational",
                 "endpoint": url, "description": str(e), "parameter": ""}]

    headers = {k.lower(): v for k, v in resp.headers.items()}

    # ── Missing security headers ───────────────────────────────────────────────
    for idx, (header, severity, desc, recommended, cweid) in enumerate(SECURITY_HEADERS, 1):
        if header.lower() not in headers:
            findings.append({
                "id":          f"hdr-{idx:03d}",
                "tool":        "headers-check",
                "vuln_type":   f"Missing Header: {header}",
                "severity":    severity,
                "endpoint":    url,
                "parameter":   header,
                "description": desc,
                "solution":    f"Add response header: {header}: {recommended}",
                "evidence":    f"Header '{header}' not present in response",
                "cweid":       cweid,
            })

    # ── Server banner disclosure ───────────────────────────────────────────────
    server = headers.get("server", "")
    if server and any(c.isdigit() for c in server):
        findings.append({
            "id":          "hdr-100",
            "tool":        "headers-check",
            "vuln_type":   "Server Version Disclosure",
            "severity":    "Low",
            "endpoint":    url,
            "parameter":   "Server",
            "description": f"Server header discloses software version: '{server}'. Attackers can target known CVEs.",
            "solution":    "Configure server to return 'Server: ' with no version info.",
            "evidence":    f"Server: {server}",
            "cweid":       "200",
        })

    # ── X-Powered-By disclosure ────────────────────────────────────────────────
    powered_by = headers.get("x-powered-by", "")
    if powered_by:
        findings.append({
            "id":          "hdr-101",
            "tool":        "headers-check",
            "vuln_type":   "Technology Disclosure (X-Powered-By)",
            "severity":    "Low",
            "endpoint":    url,
            "parameter":   "X-Powered-By",
            "description": f"X-Powered-By discloses backend technology: '{powered_by}'.",
            "solution":    "Remove or suppress the X-Powered-By header.",
            "evidence":    f"X-Powered-By: {powered_by}",
            "cweid":       "200",
        })

    # ── CORS misconfiguration ──────────────────────────────────────────────────
    acao = headers.get("access-control-allow-origin", "")
    if acao == "*":
        findings.append({
            "id":          "hdr-102",
            "tool":        "headers-check",
            "vuln_type":   "Wildcard CORS Policy",
            "severity":    "Medium",
            "endpoint":    url,
            "parameter":   "Access-Control-Allow-Origin",
            "description": "CORS policy allows any origin (*). Credentials-bearing requests from any site are permitted.",
            "solution":    "Restrict CORS to specific trusted origins.",
            "evidence":    "Access-Control-Allow-Origin: *",
            "cweid":       "942",
        })

    # Sort by severity
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.get("severity", "Low"), 3))
    return findings
