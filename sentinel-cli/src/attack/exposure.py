import re
import requests
from bs4 import BeautifulSoup

SENSITIVE_PATHS = [
    # Original paths
    "/.env",
    "/.env.local",
    "/.env.production",
    "/.git/config",
    "/.git/HEAD",
    "/swagger.json",
    "/swagger/v1/swagger.json",
    "/api/swagger.json",
    "/openapi.json",
    "/api-docs",
    "/config.json",
    "/robots.txt",
    "/sitemap.xml",
    "/.DS_Store",
    "/backup.zip",
    "/dump.sql",
    "/phpinfo.php",
    "/server-status",
    "/actuator",
    "/actuator/env",
    "/actuator/health",
    "/_next/static/chunks/",

    # === Expanded Sensitive Paths ===

    # Environment & Config Files
    "/.env.example",
    "/.env.dev",
    "/.env.development",
    "/.env.test",
    "/.env.staging",
    "/config.php",
    "/config.yaml",
    "/config.yml",
    "/settings.php",
    "/settings.py",
    "/web.config",
    "/wp-config.php",
    "/application/config/config.php",
    "/config/database.php",
    "/database.yml",
    "/secrets.json",
    "/credentials.json",
    "/appsettings.json",
    "/appsettings.Development.json",

    # Version Control
    "/.git/index",
    "/.git/logs/HEAD",
    "/.git/logs/refs/heads/main",
    "/.gitignore",
    "/.svn/entries",
    "/.hg/requires",

    # Backup & Dump Files
    "/backup.sql",
    "/database.sql",
    "/db_dump.sql",
    "/dump.sql.gz",
    "/backup.zip",
    "/site_backup.tar.gz",
    "/config.php.bak",
    "/wp-config.php.bak",
    "/index.php.bak",
    "/*.bak",
    "/*.old",
    "/*.tmp",

    # Logs & Debug
    "/debug.log",
    "/error.log",
    "/access.log",
    "/application.log",
    "/logs/error.log",
    "/debug.php",
    "/test.php",
    "/info.php",

    # Admin & Login Panels
    "/admin",
    "/admin.php",
    "/administrator",
    "/login",
    "/wp-admin",
    "/cpanel",
    "/phpmyadmin",
    "/adminer.php",
    "/backend",
    "/dashboard",
    "/manage",

    # API Documentation & Endpoints
    "/swagger-ui.html",
    "/swagger/index.html",
    "/redoc",
    "/graphiql",
    "/graphql",
    "/api/v1",
    "/api/v2",
    "/v1/swagger.json",

    # Spring Boot Actuator
    "/actuator/info",
    "/actuator/metrics",
    "/actuator/beans",
    "/actuator/mappings",
    "/actuator/loggers",
    "/actuator/heapdump",
    "/actuator/threaddump",

    # CMS & Framework Specific
    "/joomla.xml",
    "/configuration.php",
    "/elmah.axd",
    "/trace.axd",
    "/wp-content/uploads/",

    # Composer / Package Files
    "/composer.json",
    "/composer.lock",
    "/package.json",
    "/yarn.lock",
    "/Gemfile",
    "/Gemfile.lock",

    # Other Common Sensitive Paths
    "/.htaccess",
    "/.htpasswd",
    "/crossdomain.xml",
    "/clientaccesspolicy.xml",
    "/status",
    "/heapdump",
    "/vendor/",
    "/core",
    "/proc/self/environ",
    "/etc/passwd",
]




def check_exposure(target_url, console=None):
    """
    Check for exposed sensitive files and API routes.

    console=None → completely silent (used by brain.py)
    console=<Console> → prints progress to terminal (used by direct CLI calls)
    """

    def log(msg):
        # Only print if a console was explicitly provided
        # Never use plain print() — Rich markup would leak as raw text
        if console:
            console.print(msg)

    log("[yellow][*] Checking for exposed sensitive files...[/yellow]")

    findings = []
    target_url = target_url.rstrip("/")

    paths_to_check = list(SENSITIVE_PATHS)
    # Anti-False Positive Check: Does the server return 200 for EVERYTHING?
    try:
        r_test = requests.get(target_url + "/this-file-definitely-does-not-exist-999.txt", timeout=5, verify=False, allow_redirects=False)
        if r_test.status_code in [200, 301, 302]:
            log("[dim][-] Server returns 200/301 for random paths (Catch-All). Skipping static file baseline checks.[/dim]")
            paths_to_check = [] # Disable the list cleanly
    except Exception:
        pass

    for path in paths_to_check:
        try:
            url = target_url + path
            r = requests.get(url, timeout=5, verify=False,
                             allow_redirects=False)

            if r.status_code in [200, 301, 302]:
                severity = "High"
                description = f"Sensitive path accessible: {path}"

                if any(x in path for x in [".env", ".git", "swagger",
                                            "actuator", "dump.sql"]):
                    severity = "High"
                    description = f"CRITICAL exposure: {path} is accessible. "
                    if ".env" in path:
                        description += "May contain API keys, DB credentials."
                    elif ".git" in path:
                        description += "Source code may be downloadable."
                    elif "swagger" in path:
                        description += "Full API documentation exposed to attackers."
                    elif "actuator" in path:
                        description += "Spring Boot actuator exposed — server internals visible."

                findings.append({
                    "tool":          "exposure",
                    "vuln_type":     f"Exposed File: {path}",
                    "severity":      severity,
                    "endpoint":      url,
                    "method":        "GET",
                    "evidence":      f"HTTP {r.status_code}",
                    "description":   description,
                    "hacker_impact": f"Attacker can access {path} directly"
                })
                log(f"[red]  [!] FOUND: {path} → HTTP {r.status_code}[/red]")
            # Silent on misses — no log for 404s

        except Exception:
            continue

    # Extract API routes from JS bundle (Advanced parsing)
    try:
        r = requests.get(target_url, timeout=8, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Get all external scripts AND inline scripts
        js_sources = []
        for s in soup.find_all('script'):
            if s.get('src'):
                js_sources.append(s.get('src'))
            elif s.string:
                js_sources.append(('inline', s.string))

        all_routes = set()
        
        # Regex to catch robust endpoints (starts with /api, /v1, /graphql OR typical fetch/axios calls)
        path_regex = r'["\']((?:(?:/api/|/rest/|/v\d+/|/graphql)[^"\'?\s]+)|(?:https?://[^"\'?\s]+))["\']'
        fetch_regex = r'(?:fetch|axios(?:\.\w+)?|XMLHttpRequest\.open\([^,]+,)\s*\(?\s*["\']([^"\'\s]+)["\']'

        for src in js_sources[:20]: # Parse up to 20 scripts
            js = ""
            if isinstance(src, tuple) and src[0] == 'inline':
                js = src[1]
            else:
                url = target_url.rstrip('/') + src if src.startswith('/') else src
                if not url.startswith('http'):
                    url = target_url.rstrip('/') + '/' + src
                try:
                    js = requests.get(url, timeout=8, verify=False).text
                except Exception:
                    continue
            
            # Find routes
            matches = re.findall(path_regex, js)
            matches += re.findall(fetch_regex, js)
            
            for m in matches:
                url_str = m if isinstance(m, str) else m[-1]
                # Filter out obvious false positives (JS files, short strings)
                if len(url_str) > 3 and not url_str.endswith('.js') and not url_str.endswith('.html') and not url_str.endswith('.css'):
                    all_routes.add(url_str)

        if all_routes:
            findings.append({
                "tool":          "exposure",
                "vuln_type":     "API Routes Extracted from JS Bundle",
                "severity":      "Medium",
                "endpoint":      target_url,
                "method":        "GET",
                "evidence":      f"Found {len(all_routes)} API routes in JS",
                "description":   f"Script contained {len(all_routes)} hardcoded API calls/routes: {list(all_routes)[:10]}...",
                "hacker_impact": "An attacker has a map of your backend API operations without needing official documentation."
            })
            log(f"[yellow]  [!] {len(all_routes)} API calls/routes extracted from JS bundle[/yellow]")
            
    except Exception:
        pass

    log(f"[green][+] Exposure check complete — {len(findings)} findings[/green]")
    return findings