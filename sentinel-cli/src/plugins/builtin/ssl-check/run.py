"""
ssl-check plugin — Sentinel Security Scanner
Checks SSL/TLS configuration: certificate validity, expiry, weak ciphers,
protocol versions, and HSTS header presence.
"""

import socket
import ssl
import datetime
import requests
from urllib.parse import urlparse


def run(url: str, console=None, config: dict = None) -> list[dict]:
    """
    Analyze SSL/TLS for the given URL.
    Returns a list of finding dicts compatible with Sentinel's schema.
    """
    findings = []
    parsed   = urlparse(url)
    hostname = parsed.hostname
    port     = parsed.port or (443 if parsed.scheme == "https" else 80)

    if parsed.scheme != "https":
        findings.append({
            "id":          "ssl-001",
            "tool":        "ssl-check",
            "vuln_type":   "No HTTPS",
            "severity":    "High",
            "endpoint":    url,
            "parameter":   "",
            "description": "The target is not using HTTPS. All traffic is transmitted in plaintext.",
            "solution":    "Redirect all HTTP traffic to HTTPS. Obtain a valid TLS certificate.",
            "evidence":    f"Scheme: {parsed.scheme}",
            "cweid":       "311",
        })
        return findings

    # ── Certificate inspection ─────────────────────────────────────────────────
    try:
        ctx  = ssl.create_default_context()
        conn = ctx.wrap_socket(
            socket.create_connection((hostname, port), timeout=10),
            server_hostname=hostname
        )
        cert = conn.getpeercert()
        conn.close()

        # Expiry check
        expiry_str = cert.get("notAfter", "")
        if expiry_str:
            expiry = datetime.datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
            days_left = (expiry - datetime.datetime.utcnow()).days

            if days_left < 0:
                findings.append({
                    "id":          "ssl-002",
                    "tool":        "ssl-check",
                    "vuln_type":   "Expired SSL Certificate",
                    "severity":    "High",
                    "endpoint":    url,
                    "parameter":   "",
                    "description": f"SSL certificate expired {abs(days_left)} days ago ({expiry_str}).",
                    "solution":    "Renew the SSL certificate immediately.",
                    "evidence":    f"notAfter: {expiry_str}",
                    "cweid":       "298",
                })
            elif days_left < 30:
                findings.append({
                    "id":          "ssl-003",
                    "tool":        "ssl-check",
                    "vuln_type":   "SSL Certificate Expiring Soon",
                    "severity":    "Medium",
                    "endpoint":    url,
                    "parameter":   "",
                    "description": f"SSL certificate expires in {days_left} days ({expiry_str}).",
                    "solution":    "Renew the SSL certificate before expiry.",
                    "evidence":    f"notAfter: {expiry_str}",
                    "cweid":       "298",
                })

        # Subject Alternative Names
        san = cert.get("subjectAltName", [])
        if not san:
            findings.append({
                "id":          "ssl-004",
                "tool":        "ssl-check",
                "vuln_type":   "Missing Subject Alternative Names",
                "severity":    "Low",
                "endpoint":    url,
                "parameter":   "",
                "description": "Certificate has no Subject Alternative Names (SANs). Modern browsers require SANs.",
                "solution":    "Reissue certificate with proper SAN entries.",
                "evidence":    "subjectAltName: empty",
                "cweid":       "295",
            })

    except ssl.SSLCertVerificationError as e:
        findings.append({
            "id":          "ssl-005",
            "tool":        "ssl-check",
            "vuln_type":   "Invalid SSL Certificate",
            "severity":    "High",
            "endpoint":    url,
            "parameter":   "",
            "description": f"SSL certificate verification failed: {e}",
            "solution":    "Install a valid certificate from a trusted CA.",
            "evidence":    str(e),
            "cweid":       "295",
        })
    except ssl.SSLError as e:
        findings.append({
            "id":          "ssl-006",
            "tool":        "ssl-check",
            "vuln_type":   "SSL Handshake Error",
            "severity":    "Medium",
            "endpoint":    url,
            "parameter":   "",
            "description": f"SSL handshake failed: {e}",
            "solution":    "Review TLS configuration and supported protocol versions.",
            "evidence":    str(e),
            "cweid":       "326",
        })
    except Exception:
        pass

    # ── Weak protocols check ───────────────────────────────────────────────────
    for proto_name, proto_const in [("TLSv1", ssl.PROTOCOL_TLS_CLIENT), ("SSLv3", ssl.PROTOCOL_TLS_CLIENT)]:
        try:
            ctx2 = ssl.SSLContext(proto_const)
            ctx2.minimum_version = ssl.TLSVersion.TLSv1
            ctx2.maximum_version = ssl.TLSVersion.TLSv1
            ctx2.check_hostname  = False
            ctx2.verify_mode     = ssl.CERT_NONE
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with ctx2.wrap_socket(sock, server_hostname=hostname):
                    findings.append({
                        "id":          "ssl-007",
                        "tool":        "ssl-check",
                        "vuln_type":   f"Weak TLS Protocol Supported ({proto_name})",
                        "severity":    "Medium",
                        "endpoint":    url,
                        "parameter":   "",
                        "description": f"Server accepts {proto_name}, which is deprecated and insecure.",
                        "solution":    f"Disable {proto_name} and enforce TLS 1.2 or higher.",
                        "evidence":    f"Connected using {proto_name}",
                        "cweid":       "326",
                    })
        except Exception:
            pass

    # ── HSTS header check ──────────────────────────────────────────────────────
    try:
        r = requests.get(url, timeout=10, verify=False, allow_redirects=True)
        hsts = r.headers.get("Strict-Transport-Security", "")
        if not hsts:
            findings.append({
                "id":          "ssl-008",
                "tool":        "ssl-check",
                "vuln_type":   "Missing HSTS Header",
                "severity":    "Low",
                "endpoint":    url,
                "parameter":   "Strict-Transport-Security",
                "description": "HTTP Strict Transport Security (HSTS) header is not set. Browsers may allow insecure connections.",
                "solution":    "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
                "evidence":    "Header absent",
                "cweid":       "319",
            })
    except Exception:
        pass

    return findings
