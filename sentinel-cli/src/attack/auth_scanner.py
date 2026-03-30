import requests
from requests.exceptions import RequestException

def run_auth_scan(target_url, login_url=None, request_file=None, console=None):
    """
    Run deterministic Authentication baseline checks.
    """
    def log(msg):
        if console:
            console.print(msg)

    log("[yellow][*] Running Auth Scan — checking auth endpoints...[/yellow]")
    
    findings = []
    
    session = requests.Session()
    session.verify = False # Suppress SSL warnings in attacks
    
    valid_login_endpoint = None

    if login_url:
        # Use explicitly provided endpoint
        valid_login_endpoint = login_url
        log(f"[cyan][+] Using explicit auth endpoint: {valid_login_endpoint}[/cyan]")
    elif request_file:
        # Extract endpoint from captured traffic file
        try:
            from src.utils.replay import parse_raw_request, get_full_url
            with open(request_file, 'r') as f:
                method, path, headers, body = parse_raw_request(f.read())
                valid_login_endpoint = get_full_url(target_url, path)
                log(f"[cyan][+] Extracted auth endpoint from traffic file: {valid_login_endpoint}[/cyan]")
        except Exception as e:
            log(f"[dim][!] Could not parse request file for Auth Scan: {e}[/dim]")

    if not valid_login_endpoint:
        # Fallback to guessing common endpoints (Discovery)
        login_paths = [
            "/login", "/api/login", "/auth", "/api/auth", "/signin", "/user/login", "/rest/user/login"
        ]
        for path in login_paths:
            url = target_url.rstrip("/") + path
            try:
                r = session.get(url, timeout=5)
                if r.status_code in [200, 401, 403]:
                    valid_login_endpoint = url
                    log(f"[cyan][+] Discovered potential auth endpoint: {valid_login_endpoint}[/cyan]")
                    break
            except Exception:
                pass
            
    if not valid_login_endpoint:
        log("[dim][-] No valid login endpoint found or provided. Skipping deeper auth tests.[/dim]")
        return findings

    # 0. Baseline check: What does a failed login look like?
    baseline_failed_len = 0
    baseline_failed_status = 0
    try:
        r_fail = session.post(valid_login_endpoint, json={"username": "superfakeuser123999", "password": "wrongpassword123"}, timeout=5)
        baseline_failed_len = len(r_fail.text)
        baseline_failed_status = r_fail.status_code
    except Exception:
        pass

    # 2. Test common default credentials (deterministic brute check)
    default_creds = [
        ("admin", "admin"),
        ("admin", "password"),
        ("test", "test"),
        ("admin", "admin123"),
    ]
    
    found_default = False
    for user, pwd in default_creds:
        if found_default: break
        
        # Some APIs use email, some use username
        payloads = [
            {"email": f"{user}@{target_url.split('//')[-1].split(':')[0]}", "password": pwd},
            {"username": user, "password": pwd}
        ]
        
        for payload in payloads:
            try:
                r = session.post(valid_login_endpoint, json=payload, timeout=5)
                
                # Check for deviation from the baseline failed response
                is_different = (r.status_code != baseline_failed_status) or (abs(len(r.text) - baseline_failed_len) > 150)
                is_success = r.status_code in [200, 201, 301, 302] and "invalid" not in r.text.lower() and "incorrect" not in r.text.lower()
                
                if is_different and is_success:
                    findings.append({
                        "tool": "auth_scanner",
                        "vuln_type": "Default Credentials Allowed",
                        "severity": "High",
                        "endpoint": valid_login_endpoint,
                        "method": "POST",
                        "evidence": f"Successfully authenticated with payload: {payload}. Response size deviated from failed baseline.",
                        "description": "The application allows standard default credentials, which is a critical risk."
                    })
                    found_default = True
                    break # Stop if we found a working default
            except Exception:
                pass
                
    # 3. Test simple Auth Bypass SQLi
    sqli_payloads = [
        "' OR '1'='1",
        "admin' --",
        "' OR 1=1--"
    ]
    
    found_sqli = False
    for sqli in sqli_payloads:
        if found_sqli: break
        
        # SQLi typically occurs on the username field
        payload = {"email": sqli, "password": "random_password"}
        try:
            r = session.post(valid_login_endpoint, json=payload, timeout=5)
            
            is_different = (r.status_code != baseline_failed_status) or (abs(len(r.text) - baseline_failed_len) > 150)
            is_success = r.status_code in [200, 201, 301, 302] and "invalid" not in r.text.lower() and "incorrect" not in r.text.lower()
            
            if is_different and is_success:
                 findings.append({
                    "tool": "auth_scanner",
                    "vuln_type": "Authentication Bypass via SQL Injection",
                    "severity": "High",
                    "endpoint": valid_login_endpoint,
                    "method": "POST",
                    "evidence": f"Bypassed authentication using SQLi payload: {sqli}. Response structure bypassed validation.",
                    "description": "The login mechanism is vulnerable to SQL injection, allowing unauthorized access."
                 })
                 found_sqli = True
                 break # Stop if we found a working SQLi
        except Exception:
             pass

    log(f"[green][+] Auth scan complete — {len(findings)} findings[/green]")
    return findings
