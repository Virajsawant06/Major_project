import requests
import re
import json
import copy
from urllib.parse import urlparse, parse_qs, urlencode

def run_idor_scan(target_url, auth_header=None, request_file=None, console=None):
    """
    Run IDOR checks. If a request_file is provided, parse it and systematically
    mutate numeric parameters in the JSON body, Query string, and URL Path.
    """
    def log(msg):
        if console:
            console.print(msg)

    log("[yellow][*] Running IDOR Scan — testing parameter tampering...[/yellow]")
    findings = []
    
    if request_file:
        log("[cyan][+] Traffic file provided. Running Advanced Replay IDOR check...[/cyan]")
        try:
            from src.utils.replay import parse_raw_request, get_full_url, replay_request
            session = requests.Session()
            session.verify = False
            
            with open(request_file, 'r') as f:
                method, path, headers, body = parse_raw_request(f.read())
                
            url = get_full_url(target_url, path)
            
            # Get Baseline
            r_base = replay_request(method, url, headers, body, session=session)
            base_len = len(r_base.text)
            
            # --- 1. Mutate JSON Body parameters ---
            if method in ['POST', 'PUT', 'PATCH'] and body and "{" in body:
                try:
                    jbody = json.loads(body)
                    for key, val in jbody.items():
                        if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                            num_val = int(val)
                            new_val = num_val + 1 if num_val > 0 else 1
                            
                            mod_body = copy.deepcopy(jbody)
                            mod_body[key] = str(new_val) if isinstance(val, str) else new_val
                            
                            r_mod = replay_request(method, url, headers, json.dumps(mod_body), session=session)
                            
                            if r_mod.status_code == r_base.status_code and abs(len(r_mod.text) - base_len) > 5 and r_mod.text != r_base.text:
                                findings.append({
                                    "tool": "idor_scanner",
                                    "vuln_type": "JSON Body Tampering (IDOR)",
                                    "severity": "High",
                                    "endpoint": url,
                                    "method": method,
                                    "evidence": f"Changed JSON param '{key}' to {new_val}",
                                    "description": f"An attacker can access/modify other records by altering '{key}' in the JSON body."
                                })
                except Exception:
                    pass
            
            # --- 2. Mutate Query Strings ---
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            for key, vals in qs.items():
                val = vals[0]
                if val.isdigit():
                    new_val = int(val) + 1
                    mod_qs = copy.deepcopy(qs)
                    mod_qs[key] = [str(new_val)]
                    mod_url = parsed._replace(query=urlencode(mod_qs, doseq=True)).geturl()
                    
                    r_mod = replay_request(method, mod_url, headers, body, session=session)
                    if r_mod.status_code == r_base.status_code and abs(len(r_mod.text) - base_len) > 5 and r_mod.text != r_base.text:
                        findings.append({
                            "tool": "idor_scanner",
                            "vuln_type": "Query Parameter Tampering (IDOR)",
                            "severity": "High",
                            "endpoint": mod_url,
                            "method": method,
                            "evidence": f"Changed query param '{key}' to {new_val}",
                            "description": f"An attacker can read other data by altering the '{key}' query parameter."
                        })
            
            # --- 3. Mutate URL Path (e.g. /users/1 -> /users/2) ---
            path_parts = parsed.path.split('/')
            for i, part in enumerate(path_parts):
                if part.isdigit():
                    new_val = int(part) + 1
                    mod_parts = list(path_parts)
                    mod_parts[i] = str(new_val)
                    mod_url = parsed._replace(path='/'.join(mod_parts)).geturl()
                    
                    r_mod = replay_request(method, mod_url, headers, body, session=session)
                    if r_mod.status_code == r_base.status_code and abs(len(r_mod.text) - base_len) > 5 and r_mod.text != r_base.text:
                        findings.append({
                            "tool": "idor_scanner",
                            "vuln_type": "URL Path Tampering (IDOR)",
                            "severity": "High",
                            "endpoint": mod_url,
                            "method": method,
                            "evidence": f"Changed path ID {part} to {new_val}",
                            "description": "An attacker can manipulate the REST endpoint ID to access unauthorized objects."
                        })
        except Exception as e:
            log(f"[dim][!] Replay IDOR scan failed: {e}[/dim]")
            
        log(f"[green][+] Replay IDOR scan complete — {len(findings)} findings[/green]")
        return findings

    # --- Fallback to unguided generic scan if no request_file provided ---
    if not auth_header:
         log("[dim][!] No --auth-header provided. IDOR scan will run unauthenticated, which severely limits effectiveness.[/dim]")
         
    headers = {}
    if auth_header:
         # Parse --auth-header "Authorization: Bearer <token>"
         if ":" in auth_header:
             parts = auth_header.split(":", 1)
             headers[parts[0].strip()] = parts[1].strip()
         else:
             # Assume it's just the value and default to Authorization
             headers["Authorization"] = auth_header

    # List of common predictable endpoints on test apps that usually require an ID
    test_endpoints = [
        "/api/users/1",
        "/api/users/2",
        "/rest/basket/1",
        "/rest/basket/2",
        "/api/profile/1",
        "/api/profile/2"
    ]
    
    session = requests.Session()
    session.headers.update(headers)
    session.verify = False
    
    # 1. Ping the endpoints
    valid_endpoints = []
    for ep in test_endpoints:
        url = target_url.rstrip("/") + ep
        try:
             r = session.get(url, timeout=5)
             # If we get a 200 OK, the object was fetched
             if r.status_code == 200:
                 valid_endpoints.append((url, r.text, len(r.text)))
        except Exception:
             pass
             
    # 2. Check for IDOR (Insecure Direct Object Reference)
    # Finding is triggered if we can fetch multiple distinct objects from the same base path
    if len(valid_endpoints) > 1:
        baseline_resp = valid_endpoints[0]
        
        for ep_url, ep_text, ep_len in valid_endpoints[1:]:
             # Remove numbers to find the base path (e.g., /api/users/1 -> /api/users/)
             base1 = re.sub(r'\d+', '', baseline_resp[0])
             base2 = re.sub(r'\d+', '', ep_url)
             
             # If they share the same base path but the body content differs
             if base1 == base2 and abs(ep_len - baseline_resp[2]) > 5:
                  findings.append({
                        "tool": "idor_scanner",
                        "vuln_type": "Insecure Direct Object Reference (IDOR)",
                        "severity": "High",
                        "endpoint": ep_url,
                        "method": "GET",
                        "evidence": f"Successfully accessed multiple numeric IDs on {base1} with same credentials.",
                        "description": "An attacker can likely read or manipulate other users' data by changing numeric IDs in the URL."
                  })
                  # Report once per base path to avoid flooding
                  break 

    log(f"[green][+] IDOR scan complete — {len(findings)} findings[/green]")
    return findings
