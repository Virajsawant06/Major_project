"""
Sentinel Plugin Manager
Handles install / list / run of skill plugins.

Plugin locations (in priority order):
  1. ~/.sentinel/plugins/<name>/        (user-installed)
  2. <sentinel-package>/builtin_plugins/ (shipped with sentinel)

Each plugin directory must contain:
  plugin.json  — manifest
  run.py       — exports run(url, console, config) -> list[dict]
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from src.config import manager as cfg

# ── Built-in plugin registry ───────────────────────────────────────────────────
# These are shipped inside the sentinel package. Installable plugins are
# downloaded from GitHub gists / git repos defined here.

BUILTIN_PLUGINS_DIR = Path(__file__).parent / "builtin"

REGISTRY = {
    "ssl-check": {
        "description": "SSL/TLS certificate analysis — expiry, weak ciphers, HSTS",
        "version":     "1.0.0",
        "author":      "sentinel-core",
        "builtin":     True,
        "requires":    ["sslyze"],
    },
    "headers-check": {
        "description": "HTTP security headers audit — CSP, HSTS, X-Frame-Options, etc.",
        "version":     "1.0.0",
        "author":      "sentinel-core",
        "builtin":     True,
        "requires":    ["requests"],
    },
    "nuclei": {
        "description": "Project Discovery Nuclei — runs community templates for known CVEs",
        "version":     "1.0.0",
        "author":      "sentinel-core",
        "builtin":     True,
        "requires":    ["nuclei binary (https://github.com/projectdiscovery/nuclei)"],
        "binary":      "nuclei",
    },
    "subfinder": {
        "description": "Subdomain enumeration via Project Discovery subfinder",
        "version":     "1.0.0",
        "author":      "sentinel-core",
        "builtin":     True,
        "requires":    ["subfinder binary (https://github.com/projectdiscovery/subfinder)"],
        "binary":      "subfinder",
    },
    "wayback": {
        "description": "Fetch historical endpoints from the Wayback Machine",
        "version":     "1.0.0",
        "author":      "sentinel-core",
        "builtin":     True,
        "requires":    ["requests"],
    },
    "cors-check": {
        "description": "CORS misconfiguration scanner",
        "version":     "1.0.0",
        "author":      "sentinel-core",
        "builtin":     True,
        "requires":    ["requests"],
    },
}


# ── Plugin resolution ──────────────────────────────────────────────────────────

def _user_plugin_dir(name: str) -> Path:
    return cfg.PLUGINS_DIR / name


def _builtin_plugin_dir(name: str) -> Path:
    return BUILTIN_PLUGINS_DIR / name


def is_installed(name: str) -> bool:
    """Check if a plugin is installed (user dir or built-in)."""
    if _user_plugin_dir(name).exists():
        return True
    if _builtin_plugin_dir(name).exists():
        return True
    return False


def list_plugins() -> list[dict]:
    """
    Return all known plugins with install status.
    """
    plugins = []
    seen = set()

    # Registry plugins
    for name, meta in REGISTRY.items():
        installed = is_installed(name)
        # Check if required binary is available
        binary_ok = True
        binary = meta.get("binary")
        if binary and installed:
            binary_ok = shutil.which(binary) is not None

        plugins.append({
            "name":        name,
            "description": meta["description"],
            "version":     meta["version"],
            "author":      meta["author"],
            "installed":   installed,
            "binary_ok":   binary_ok,
            "binary":      binary,
        })
        seen.add(name)

    # User-installed plugins not in registry
    if cfg.PLUGINS_DIR.exists():
        for d in cfg.PLUGINS_DIR.iterdir():
            if d.is_dir() and d.name not in seen:
                manifest = d / "plugin.json"
                if manifest.exists():
                    with open(manifest, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    plugins.append({
                        "name":        d.name,
                        "description": meta.get("description", ""),
                        "version":     meta.get("version", "?"),
                        "author":      meta.get("author", "community"),
                        "installed":   True,
                        "binary_ok":   True,
                        "binary":      None,
                    })

    return plugins


def install(name: str) -> tuple[bool, str]:
    """
    Install a plugin. For built-in plugins, copies from builtin dir to user dir.
    Returns (success, message).
    """
    cfg._ensure_dirs()

    # Already in built-in registry → copy to user plugins dir (makes it "active")
    builtin_dir = _builtin_plugin_dir(name)
    user_dir    = _user_plugin_dir(name)

    if builtin_dir.exists():
        if user_dir.exists():
            return True, f"Plugin '{name}' is already installed."
        shutil.copytree(str(builtin_dir), str(user_dir))
        return True, f"Plugin '{name}' installed successfully."

    if name in REGISTRY:
        meta = REGISTRY[name]
        # Built-in plugin files should exist; if not, they haven't been written yet
        return False, (
            f"Plugin '{name}' is registered but its files are not found. "
            f"Ensure the sentinel package is up to date."
        )

    return False, f"Unknown plugin '{name}'. Run 'sentinel plugins list' to see available plugins."


def uninstall(name: str) -> tuple[bool, str]:
    """Remove a user-installed plugin."""
    user_dir = _user_plugin_dir(name)
    if user_dir.exists():
        shutil.rmtree(str(user_dir))
        return True, f"Plugin '{name}' uninstalled."
    return False, f"Plugin '{name}' is not installed in user directory."


def run_plugin(name: str, url: str, console=None) -> list[dict]:
    """
    Load and execute a plugin's run() function.
    Returns list of finding dicts.
    """
    # Resolve plugin dir
    plugin_dir = None
    for candidate in [_user_plugin_dir(name), _builtin_plugin_dir(name)]:
        if candidate.exists():
            plugin_dir = candidate
            break

    if plugin_dir is None:
        raise FileNotFoundError(
            f"Plugin '{name}' not found. Install it first: sentinel plugins install {name}"
        )

    run_file = plugin_dir / "run.py"
    if not run_file.exists():
        raise FileNotFoundError(f"Plugin '{name}' has no run.py.")

    # Dynamically load the plugin module
    spec   = importlib.util.spec_from_file_location(f"sentinel_plugin_{name}", str(run_file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "run"):
        raise AttributeError(f"Plugin '{name}' run.py must export a run(url, console, config) function.")

    config = cfg.all_settings()
    findings = module.run(url, console=console, config=config)
    return findings or []
