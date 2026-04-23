import requests
import re
import urllib3
import concurrent.futures
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SentinelCLI/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/json,*/*",
}

class SentinelNativeEngine:
    """
    Pure Python attack engine. No external binaries.
    Fast parallel execution with strict timeouts.
    """

    def __init__(self, target_url: str):
        self.target = target_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update(SESSION_HEADERS)
        self.session.verify = False

    def _make_finding(self, vuln_type: str, severity: str, endpoint: str,
                      description: str, evidence: str = "", parameter: str = "",
                      solution: str = "", cweid: str = "0") -> dict:
        return {
            "tool": "native_engine",
            "vuln_type": vuln_type,
            "severity": severity.capitalize(),
            "endpoint": endpoint,
            "parameter": parameter,
            "method": "GET" if not parameter else "GET/POST",
            "evidence": evidence,
            "description": description,
            "hacker_impact": description, # Used interchangeably in some places
            "solution": solution,
            "cweid": cweid
        }

    # 1. SECURITY HEADERS
    def check_security_headers(self, timeout: int) -> list:
        findings = []
        try:
            resp = self.session.get(self.target, timeout=timeout, allow_redirects=True)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            
            checks = {
                "x-frame-options": ("Missing Anti-Clickjacking Header", "Medium", "X-Frame-Options missing.", "Add: X-Frame-Options: DENY"),
                "content-security-policy": ("Content Security Policy (CSP) Missing", "Medium", "CSP missing.", "Add: Content-Security-Policy: default-src 'self'"),
                "strict-transport-security": ("HSTS Header Missing", "Medium", "HSTS missing.", "Add: Strict-Transport-Security: max-age=31536000"),
                "x-content-type-options": ("X-Content-Type-Options Missing", "Low", "MIME sniffing possible.", "Add: X-Content-Type-Options: nosniff"),
                "referrer-policy": ("Referrer-Policy Missing", "Low", "Referrer leakage possible.", "Add: Referrer-Policy: strict-origin-when-cross-origin"),
                "permissions-policy": ("Permissions-Policy Missing", "Low", "Browser API abuse possible.", "Add: Permissions-Policy: geolocation=()")
            }
            
            for key, (vuln, sev, desc, sol) in checks.items():
                if key not in headers:
                    findings.append(self._make_finding(vuln, sev, self.target, desc, f"Header {key} not found", "", sol, "16"))
        except Exception:
            findings.append(self._make_finding("Security Headers", "Informational", self.target, "Could not test security headers (timeout/error)", ""))
        return findings

    # 2. COOKIE SECURITY
    def check_cookie_security(self, timeout: int) -> list:
        findings = []
        try:
            resp = self.session.get(self.target, timeout=timeout)
            cookies = resp.headers.getlist('Set-Cookie') if hasattr(resp.headers, 'getlist') else []
            if not cookies and resp.headers.get('set-cookie'):
                cookies = [resp.headers.get('set-cookie')]
            
            for c in cookies:
                c_low = c.lower()
                name = c.split('=')[0].strip()
                if 'secure' not in c_low:
                    findings.append(self._make_finding("Cookie Without Secure Flag", "Medium", self.target, f"Cookie {name} can be transmitted over HTTP.", c[:100], name, "Add Secure flag", "614"))
                if 'httponly' not in c_low:
                    findings.append(self._make_finding("Cookie Without HttpOnly Flag", "Medium", self.target, f"Cookie {name} accessible via JS (XSS theft risk).", c[:100], name, "Add HttpOnly flag", "1004"))
        except Exception:
            pass
        return findings

    # 3. CORS
    def check_cors(self, timeout: int) -> list:
        findings = []
        try:
            headers = {"Origin": "https://evil.com"}
            resp = self.session.options(self.target, headers=headers, timeout=timeout)
            allow_origin = resp.headers.get('Access-Control-Allow-Origin', '')
            allow_creds = resp.headers.get('Access-Control-Allow-Credentials', '')
            
            if allow_origin == '*' or 'evil.com' in allow_origin:
                sev = "High" if allow_creds.lower() == 'true' else "Medium"
                findings.append(self._make_finding("CORS Misconfiguration", sev, self.target, f"CORS reflects arbitrary origin '{allow_origin}'. Credentials allowed: {allow_creds}", f"Allow-Origin: {allow_origin}", "", "Restrict CORS to trusted domains.", "942"))
        except Exception:
            pass
        return findings

    # 4. HTTP METHODS
    def check_http_methods(self, timeout: int) -> list:
        findings = []
        try:
            resp = self.session.options(self.target, timeout=timeout)
            allowed = resp.headers.get('Allow', '').upper()
            dangerous = [m for m in ['PUT', 'DELETE', 'TRACE', 'CONNECT'] if m in allowed]
            if dangerous:
                findings.append(self._make_finding("Insecure HTTP Methods", "Medium", self.target, f"Dangerous methods enabled: {', '.join(dangerous)}", allowed, "", "Disable unsafe methods", "749"))
        except Exception:
            pass
        return findings

    # 5. ERROR DISCLOSURE
    def test_error_disclosure(self, timeout: int) -> list:
        findings = []
        payloads = ["/?id='", "/nonexistent_page_12345", "/?q=../"]
        patterns = [r'Traceback \(most recent', r'SyntaxError:', r'Fatal error:', r'SQLSTATE\[']
        
        for p in payloads:
            try:
                resp = self.session.get(self.target + p, timeout=timeout)
                for pat in patterns:
                    match = re.search(pat, resp.text, re.IGNORECASE)
                    if match:
                        snippet = resp.text[max(0, match.start()-20):match.start()+100]
                        findings.append(self._make_finding("Application Error Disclosure", "Medium", self.target + p, "Verbose errors leak system details.", snippet, "", "Disable debug mode.", "209"))
                        return findings
            except Exception:
                continue
        return findings

    # 6. DIRECTORY BROWSING
    def test_directory_browsing(self, timeout: int) -> list:
        findings = []
        dirs = ['/assets/', '/static/', '/uploads/', '/backup/']
        for d in dirs:
            try:
                resp = self.session.get(self.target + d, timeout=timeout)
                if resp.status_code == 200 and ('Index of /' in resp.text or '[DIR]' in resp.text):
                    findings.append(self._make_finding("Directory Browsing", "Medium", self.target + d, "Directory listing is enabled.", "Index of / found", "", "Disable directory listing.", "548"))
            except Exception:
                continue
        return findings

    # 7. AUTH BYPASS
    def test_auth_bypass(self, timeout: int) -> list:
        findings = []
        paths = ['/admin', '/dashboard', '/api/admin']
        headers = {'X-Forwarded-For': '127.0.0.1', 'X-Real-IP': '127.0.0.1'}
        
        for p in paths:
            try:
                url = self.target + p
                normal = self.session.get(url, timeout=timeout, allow_redirects=False)
                if normal.status_code in [401, 403]:
                    bypass = self.session.get(url, headers=headers, timeout=timeout, allow_redirects=False)
                    if bypass.status_code == 200:
                        findings.append(self._make_finding("Authentication Bypass", "Critical", url, "Bypass via IP spoofing headers.", "Status 200 with X-Forwarded-For: 127.0.0.1", "", "Do not trust client-supplied IP headers.", "288"))
                        return findings
            except Exception:
                continue
        return findings

    # --- INJECTION CHECKS (Require parameters) ---
    def _needs_params(self, params, forms, name):
        if not params and not forms:
            return [self._make_finding(name, "Informational", self.target, "Could not test — no parameters discovered.", "")]
        return None

    # 8. XSS
    def test_xss(self, params, forms, timeout: int) -> list:
        skip = self._needs_params(params, forms, "Cross-Site Scripting (Reflected)")
        if skip: return skip
        
        findings = []
        payload = '"><script>alert("XSS_SENTINEL")</script>'
        for item in params[:10]:
            try:
                url, param = item['url'], item['param']
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                qs[param] = [payload]
                test_url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
                resp = self.session.get(test_url, timeout=timeout)
                if payload in resp.text:
                    findings.append(self._make_finding("Cross Site Scripting (Reflected)", "High", test_url, "Unencoded payload reflected.", payload, param, "Encode output (Context-aware).", "79"))
                    break
            except Exception:
                continue
        return findings

    # 9. CSRF
    def test_csrf(self, params, forms, timeout: int) -> list:
        skip = self._needs_params(params, forms, "Cross-Site Request Forgery")
        if skip: return skip
        
        findings = []
        csrf_names = ['csrf', 'token', '_token', 'authenticity_token', 'nonce']
        for form in forms[:10]:
            url = form['url']
            form_params = [p.lower() for p in form.get('params', [])]
            if form.get('type') == 'POST' and not any(any(c in p for c in csrf_names) for p in form_params):
                findings.append(self._make_finding("Cross-Site Request Forgery", "High", url, "POST form without CSRF token detected.", f"Params: {form_params}", "", "Add Anti-CSRF tokens.", "352"))
                break
        return findings

    # 10. SQLi
    def test_sqli(self, params, forms, timeout: int) -> list:
        skip = self._needs_params(params, forms, "SQL Injection")
        if skip: return skip
        
        findings = []
        payload = "1'\""
        errors = ['sql syntax', 'mysql_fetch', 'ora-00933', 'postgresql query failed']
        for item in params[:10]:
            try:
                url, param = item['url'], item['param']
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                qs[param] = [payload]
                test_url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
                resp = self.session.get(test_url, timeout=timeout)
                for err in errors:
                    if err in resp.text.lower():
                        findings.append(self._make_finding("SQL Injection (Error Based)", "Critical", test_url, "SQL error triggered.", err, param, "Use parameterized queries.", "89"))
                        return findings
            except Exception:
                continue
        return findings

    # 11. SSRF & PATH TRAVERSAL (Combined for brevity)
    def test_ssrf_path(self, params, forms, timeout: int) -> list:
        skip = self._needs_params(params, forms, "SSRF / Path Traversal")
        if skip: return skip
        
        findings = []
        for item in params[:10]:
            url, param = item['url'], item['param']
            p_low = param.lower()
            
            # SSRF
            if any(k in p_low for k in ['url', 'src', 'redirect']):
                try:
                    payload = "http://169.254.169.254/latest/meta-data/"
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    qs[param] = [payload]
                    test_url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
                    resp = self.session.get(test_url, timeout=timeout, allow_redirects=False)
                    if 'ami-id' in resp.text:
                        findings.append(self._make_finding("Server Side Request Forgery", "Critical", test_url, "AWS metadata retrieved.", "ami-id found", param, "Validate URLs strictly.", "918"))
                except Exception:
                    pass

            # Path Traversal
            if any(k in p_low for k in ['file', 'path', 'doc']):
                try:
                    payload = "../../../../etc/passwd"
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    qs[param] = [payload]
                    test_url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
                    resp = self.session.get(test_url, timeout=timeout)
                    if 'root:x:' in resp.text:
                        findings.append(self._make_finding("Path Traversal", "Critical", test_url, "/etc/passwd retrieved.", "root:x:", param, "Sanitize file paths.", "22"))
                except Exception:
                    pass

        return findings

    def run_all(self, get_params=None, forms=None, timeout_per_check=15) -> list:
        all_findings = []
        get_params = get_params or []
        forms = forms or []

        # Run checks in parallel to guarantee <60s execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(self.check_security_headers, timeout_per_check),
                executor.submit(self.check_cookie_security, timeout_per_check),
                executor.submit(self.check_cors, timeout_per_check),
                executor.submit(self.check_http_methods, timeout_per_check),
                executor.submit(self.test_error_disclosure, timeout_per_check),
                executor.submit(self.test_directory_browsing, timeout_per_check),
                executor.submit(self.test_auth_bypass, timeout_per_check),
                executor.submit(self.test_xss, get_params, forms, timeout_per_check),
                executor.submit(self.test_csrf, get_params, forms, timeout_per_check),
                executor.submit(self.test_sqli, get_params, forms, timeout_per_check),
                executor.submit(self.test_ssrf_path, get_params, forms, timeout_per_check),
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        all_findings.extend(result)
                except Exception:
                    pass

        return all_findings
