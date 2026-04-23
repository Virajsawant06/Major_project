"""
Sentinel Config Manager
~/.sentinel/config.json — persistent user configuration
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime

# ── Sentinel home directory ────────────────────────────────────────────────────
SENTINEL_HOME = Path.home() / ".sentinel"
CONFIG_FILE   = SENTINEL_HOME / "config.json"
SCANS_DIR     = SENTINEL_HOME / "scans"
PLUGINS_DIR   = SENTINEL_HOME / "plugins"
LOGS_DIR      = SENTINEL_HOME / "logs"
LOG_FILE      = LOGS_DIR / "sentinel.log"

# ── Default configuration ──────────────────────────────────────────────────────
DEFAULTS = {
    "zap_host":          "http://127.0.0.1",
    "zap_port":          8080,
    "zap_api_key":       "",
    "ai_provider":       "openrouter",          # openrouter | ollama
    "openrouter_model":  "nvidia/nemotron-super-49b-v1:free",
    "ollama_host":       "http://localhost:11434",
    "ollama_model":      "",                    # user must set this
    "report_format":     "json",               # json | html | md
    "scan_mode":         "deep",               # fast | deep | stealth
    "max_findings":      200,
    "auto_patches":      False,
    "theme":             "dark",
}

# ── Human-readable descriptions ────────────────────────────────────────────────
CONFIG_DESCRIPTIONS = {
    "zap_host":          "ZAP daemon host",
    "zap_port":          "ZAP daemon port",
    "zap_api_key":       "ZAP API key (leave empty if none)",
    "ai_provider":       "AI provider: openrouter | ollama",
    "openrouter_model":  "OpenRouter model for cloud AI",
    "ollama_host":       "Ollama API host URL",
    "ollama_model":      "Local Ollama model (e.g. llama3, mistral, deepseek-r1)",
    "report_format":     "Default report format: json | html | md",
    "scan_mode":         "Default scan mode: fast | deep | stealth",
    "max_findings":      "Maximum findings to collect per scan",
    "auto_patches":      "Automatically generate patches after scan",
    "theme":             "Terminal theme: dark | light",
}


def _ensure_dirs():
    """Create all ~/.sentinel/* directories if they don't exist."""
    for d in [SENTINEL_HOME, SCANS_DIR, PLUGINS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict:
    """Load config JSON, return empty dict if missing."""
    _ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_raw(data: dict):
    """Write config dict to disk."""
    _ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get(key: str, fallback=None):
    """Get a config value. Falls back to DEFAULTS, then to fallback."""
    raw = _load_raw()
    if key in raw:
        return raw[key]
    if key in DEFAULTS:
        return DEFAULTS[key]
    # Also check environment variables (SENTINEL_<KEY_UPPER>)
    env_key = f"SENTINEL_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        return env_val
    # Fallback to .env values for known keys
    if key == "zap_port":
        return int(os.environ.get("ZAP_PORT", DEFAULTS["zap_port"]))
    return fallback


def set(key: str, value):
    """Set a config value and persist to disk."""
    if key not in DEFAULTS:
        raise KeyError(f"Unknown config key: '{key}'. Run 'sentinel config show' to see valid keys.")
    raw = _load_raw()
    # Type coercion
    expected = type(DEFAULTS[key])
    if expected == bool:
        if isinstance(value, str):
            value = value.lower() in ("true", "1", "yes")
    elif expected == int:
        value = int(value)
    raw[key] = value
    _save_raw(raw)


def reset():
    """Reset all config to defaults."""
    _save_raw({})


def all_settings() -> dict:
    """Return merged config (user overrides + defaults)."""
    raw = _load_raw()
    merged = {**DEFAULTS, **raw}
    return merged


def zap_url() -> str:
    """Construct full ZAP base URL."""
    host = get("zap_host")
    port = get("zap_port")
    return f"{host}:{port}"


# ── Scan storage ───────────────────────────────────────────────────────────────

def new_scan_dir(target_url: str) -> Path:
    """
    Create a timestamped scan directory.
    Format: ~/.sentinel/scans/YYYY-MM-DD_HH-MM-SS_<slug>/
    Returns the Path object.
    """
    _ensure_dirs()
    slug = target_url.replace("https://", "").replace("http://", "")
    slug = "".join(c if c.isalnum() or c in "-_." else "_" for c in slug)[:40]
    ts   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    scan_dir = SCANS_DIR / f"{ts}_{slug}"
    scan_dir.mkdir(parents=True, exist_ok=True)
    return scan_dir


def list_scans() -> list[dict]:
    """Return list of past scans, newest first."""
    _ensure_dirs()
    scans = []
    for d in sorted(SCANS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        meta_file = d / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["_dir"] = str(d)
                meta["_id"]  = d.name
                scans.append(meta)
            except Exception:
                pass
        else:
            # Fallback for scans without meta
            scans.append({
                "_dir":   str(d),
                "_id":    d.name,
                "target": d.name.split("_", 2)[-1] if "_" in d.name else d.name,
                "scanned_at": d.name[:19].replace("_", "T"),
            })
    return scans


def get_scan_dir(scan_id: str) -> Path | None:
    """Find scan dir by ID or partial match. Returns None if not found."""
    _ensure_dirs()
    # Exact match
    exact = SCANS_DIR / scan_id
    if exact.exists():
        return exact
    # Partial match (user can type partial scan-id)
    for d in SCANS_DIR.iterdir():
        if scan_id in d.name:
            return d
    return None


def latest_scan_dir() -> Path | None:
    """Return the most recent scan directory."""
    _ensure_dirs()
    dirs = sorted(
        [d for d in SCANS_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True
    )
    return dirs[0] if dirs else None


# ── Logging ────────────────────────────────────────────────────────────────────

def log(message: str, level: str = "INFO"):
    """Append a log line to ~/.sentinel/logs/sentinel.log."""
    _ensure_dirs()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
