<div align="center">

<h1>🛡️ Sentinel — AI-Powered Security Suite</h1>

<p>
  <strong>Professional security auditing. Two delivery modes. One unified platform.</strong><br/>
  Combining a blazing-fast terminal CLI with a full-stack web dashboard — powered by AI.
</p>

<p>
  <img src="https://img.shields.io/badge/version-0.2.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/python-3.9+-green?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/node-20.x-green?style=for-the-badge&logo=node.js" />
  <img src="https://img.shields.io/badge/npm-sentinel--security-red?style=for-the-badge&logo=npm" />
  <img src="https://img.shields.io/badge/docker-ready-blue?style=for-the-badge&logo=docker" />
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" />
</p>

<h3>🚀 <a href="https://sentinel-live-preview.netlify.app/">Live Platform Preview</a></h3>

<p>
  <a href="#sentinel-cli"><strong>CLI →</strong></a> ·
  <a href="#sentinel-web-shieldsentinel"><strong>Web →</strong></a> ·
  <a href="#quick-start"><strong>Quick Start →</strong></a> ·
  <a href="#installation"><strong>Installation →</strong></a>
</p>

</div>

---

## Overview

**Sentinel** is a comprehensive, AI-augmented security testing platform built for ethical hackers, security researchers, and developers who need real, actionable vulnerability data — not guesses.

The platform ships in **two modes**:

| Mode | Name | Best For |
|---|---|---|
| **Terminal CLI** | `sentinel-cli` | Hackers, pentesters, CI/CD pipelines |
| **Web Dashboard** | `SecureWithAI / ShieldSentinel` | Teams, developers, project managers |

Both share the same philosophy: **real results, zero fluff, AI-powered remediation.**

---

## Table of Contents

- [Sentinel CLI](#sentinel-cli)
  - [Features](#cli-features)
  - [Architecture](#cli-architecture)
  - [Installation — NPM](#installation--npm)
  - [Installation — Docker](#installation--docker)
  - [Usage & Commands](#usage--commands)
  - [AI Model Configuration](#ai-model-configuration)
- [Sentinel Web — ShieldSentinel](#sentinel-web--shieldsentinel)
  - [Features](#web-features)
  - [Tech Stack](#tech-stack)
  - [Architecture Diagrams](#architecture-diagrams)
  - [Running Locally](#running-locally-with-docker-compose)
  - [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [Ethics & Legal](#ethics--legal)
- [License](#license)

---

## Sentinel CLI

> A production-ready terminal security scanner. Run it anywhere Python or Docker is available.

### CLI Features

| Category | What Sentinel Does |
|---|---|
| 🔍 **DAST Scanning** | SQL Injection, XSS, CSRF, SSRF, IDOR, Open Redirect detection |
| 🔐 **Exposure Checks** | Sensitive file exposure, admin panel discovery, debug endpoint detection |
| 🔒 **Header Analysis** | Missing security headers, CSP, HSTS, X-Frame-Options |
| 🛡️ **SSL/TLS Audit** | Certificate chain, protocol version, cipher suite validation |
| 🧬 **Auth Testing** | Brute-force detection, login flow analysis, session management |
| 💉 **Injection Testing** | SQLMap integration, parameter extraction, payload fuzzing |
| 🤖 **AI Patch Engine** | Generates actionable, copy-paste ready code fixes per vulnerability |
| 💬 **AI Chat** | Interactive Q&A about your scan results with full context |
| 📊 **Scan Comparison** | Security diff between two scans — track what you fixed |
| 🔌 **Plugin System** | Nuclei, Subfinder, built-in header/SSL/subdomain plugins |

### CLI Architecture

```
sentinel-cli/
├── src/
│   ├── attack/             # Native vulnerability scanner engine
│   │   ├── native_engine.py    # Parallel execution of 11+ checks
│   │   ├── exposure.py         # File & endpoint exposure
│   │   ├── idor_scanner.py     # IDOR/access control checks
│   │   ├── auth_scanner.py     # Authentication testing
│   │   └── param_extractor.py  # JS bundle parameter mining
│   ├── intelligence/       # AI orchestration layer
│   │   ├── brain.py            # Main AI scan engine
│   │   ├── models.py           # ⭐ Central AI model registry
│   │   ├── chat_engine.py      # Interactive AI chat
│   │   └── compare_engine.py   # Scan diff & comparison
│   ├── patch/              # AI remediation engine
│   │   ├── engine.py           # Patch generation via LLM
│   │   └── ui.py               # Rich terminal UI for patches
│   ├── cli/                # Interactive shell
│   │   ├── shell.py            # REPL with prompt_toolkit
│   │   └── app.py              # Typer CLI commands
│   ├── plugins/            # Plugin ecosystem
│   │   ├── builtin/nuclei/
│   │   ├── builtin/ssl-check/
│   │   ├── builtin/subfinder/
│   │   └── builtin/headers-check/
│   ├── config/             # Config & scan storage
│   └── main.py             # Entry point
├── Dockerfile
├── docker-compose.yml
├── package.json            # NPM wrapper
└── requirements.txt
```

---

## Installation — NPM

The easiest way to install Sentinel globally. Works on Windows, macOS, and Linux.

### Prerequisites
- Node.js v16+
- Python 3.9+

### Install

```bash
npm install -g sentinel-security
```

> The post-install script automatically creates a Python virtual environment at `~/.sentinel/venv` and installs all dependencies.

### Set your API Key

Get a **free** API key at [openrouter.ai/keys](https://openrouter.ai/keys), then:

```bash
# Windows (PowerShell)
$env:OPENROUTER_API_KEY="sk-or-your-key"

# macOS / Linux
export OPENROUTER_API_KEY="sk-or-your-key"
```

### Run

```bash
sentinel
```

> For the full NPM installation guide including troubleshooting, see [`NPM-INSTALL-GUIDE.md`](sentinel-cli/NPM-INSTALL-GUIDE.md).

---

## Installation — Docker

The Docker version is the most powerful option — it bundles everything including ZAP, Nuclei, and Subfinder. No local dependencies required beyond Docker Desktop.

### Build the image

```bash
git clone https://github.com/your-repo/Major_project.git
cd Major_project/sentinel-cli
docker build -t sentinel-security:latest .
```

### Run

```bash
docker run -it -e OPENROUTER_API_KEY=sk-or-your-key sentinel-security
```

### Run with persistent scan history

```bash
# Windows (PowerShell)
docker run -it `
  -v ${HOME}/.sentinel/scans:/root/.sentinel/scans `
  -e OPENROUTER_API_KEY=sk-or-your-key `
  sentinel-security
```

### What's bundled inside the Docker image

| Tool | Version | Purpose |
|---|---|---|
| Ubuntu | 22.04 | Base OS |
| Python | 3.10 | Core engine |
| Java (OpenJDK) | 11 | ZAP runtime |
| OWASP ZAP | 2.15.0 | Deep DAST scanning |
| Nuclei | 3.3.0 | Template-based scanning |
| Subfinder | 2.6.6 | Subdomain enumeration |
| Node.js | 20.x | NPM wrapper |

> For the full Docker guide including Docker Hub publishing steps, see [`DOCKER-INSTALL-GUIDE.md`](sentinel-cli/DOCKER-INSTALL-GUIDE.md).

---

## Usage & Commands

Once installed, type `sentinel` to enter the interactive shell. All commands can also be run directly.

### CLI Commands

```bash
# Run a fast security scan (Native engine, ~60-90 seconds)
sentinel scan --url https://example.com

# Run a deep scan (Native + ZAP + Nikto, ~10 minutes)
sentinel scan --url https://example.com --mode deep

# Generate AI-powered code patches for all findings
sentinel patches

# Start an interactive AI chat about your last scan
sentinel chat

# Compare two scans to see security progress
sentinel compare <scan-id-1> <scan-id-2>

# View your scan history
sentinel history

# Run system health check (ZAP, API keys, etc.)
sentinel doctor

# Manage configuration settings
sentinel config show
sentinel config set scan_mode fast
```

### Interactive Shell Commands

Once inside the `sentinel` shell, you can also use:

```
help        — Show all available commands
scan        — Start a new scan
patches     — Generate AI patches for last scan
chat        — Enter AI chat mode
compare     — Diff two scans
history     — List past scans
cls         — Clear the screen
exit        — Exit the shell
```

### Scan Modes

| Mode | Flag | Time | Description |
|---|---|---|---|
| Fast | `--mode fast` | ~90 sec | Native Python engine only |
| Deep | `--mode deep` | ~10 min | Native + ZAP + Nikto |

---

## AI Model Configuration

Sentinel uses a **centralized model registry** at `src/intelligence/models.py`. You can change models for the entire app by editing one file — similar to a `.env` but for AI.

```python
# sentinel-cli/src/intelligence/models.py

# Model for the final hacker analysis/summary
SUMMARY_MODEL = "nvidia/nemotron-nano-9b-v2:free"

# Model for generating precise code patches
PATCH_MODEL = "nvidia/nemotron-nano-9b-v2:free"

# Model for the interactive AI chat
CHAT_MODEL = "nvidia/nemotron-nano-9b-v2:free"

# Default fallback model
PRIMARY_MODEL = "nvidia/nemotron-nano-9b-v2:free"
```

All models are called via **OpenRouter**, giving you access to hundreds of models (free and paid) from a single API key. Browse models at [openrouter.ai/models](https://openrouter.ai/models).

---

---

## Sentinel Web — ShieldSentinel

> A full-stack security testing platform with a modern React dashboard, real-time scanning, and an in-browser IDE for code fixing.

### Web Features

| Feature | Description |
|---|---|
| 🌐 **URL Scanning (DAST)** | Queue and monitor live web application scans |
| 📦 **ZIP & GitHub Scanning (SAST)** | Upload a code archive or link a GitHub repo for static analysis |
| 📊 **Real-time Dashboard** | Live scan progress via WebSocket, risk scores, KPI charts |
| 🤖 **AI Chat on Scans** | Chat with an LLM about specific findings in context |
| 🛠️ **In-Browser IDE** | Monaco editor with finding annotations and one-click AI fixes |
| 📄 **Report Export** | Download PDF or JSON reports per scan |
| 📅 **Scheduled Scans** | Schedule recurring scans with cron-based triggers |
| 🔍 **Scan Comparison** | Compare two scans to visualize security improvement |
| 🔐 **Auth** | Email/password + Google OAuth, JWT sessions, API key support |
| 📋 **Compliance** | Compliance summary per scan result |

### Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, React Router, TanStack Query, Framer Motion, Monaco Editor, Recharts, Tailwind |
| **Backend** | Python 3, FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, Redis, HTTPX |
| **Workers** | Celery (queues: `recon`, `dast`, `sast`, `ai`, `reports`) |
| **Database** | PostgreSQL 15 |
| **Scanners** | OWASP ZAP, Nuclei, Nikto, SQLMap, FFuf, Gobuster, Semgrep, Bandit, Gitleaks, Trivy + 40 more |
| **Edge** | Nginx (rate limiting, `/api`, `/ws`, static proxy) |
| **Auth** | JWT (HttpOnly cookie), Google OAuth |

### Architecture Diagrams

#### Deployment Topology

```mermaid
flowchart LR
  subgraph client [Browser]
    SPA[React / Vite]
  end
  subgraph edge [Nginx — port 99]
    NGINX[Nginx Gateway]
  end
  subgraph app [Application]
    WEB[Vite dev :9998]
    API[FastAPI :9997]
  end
  subgraph workers [Celery Workers]
    WD[worker-dast]
    WS[worker-sast]
    WA[worker-ai]
    BT[beat scheduler]
  end
  subgraph data [Data & Tools]
    PG[(PostgreSQL)]
    RD[(Redis)]
    ZAP[OWASP ZAP]
  end
  SPA --> NGINX
  NGINX --> WEB
  NGINX --> API
  SPA -->|WebSocket| API
  API --> PG
  API --> RD
  API --> workers
  WD --> ZAP
  workers --> PG
  workers --> RD
```

#### Scan Pipeline

```mermaid
sequenceDiagram
  participant User as Browser
  participant API as FastAPI
  participant DB as PostgreSQL
  participant Redis as Redis
  participant Worker as Celery Worker

  User->>API: POST /api/v1/scans/url
  API->>DB: Insert Scan (status: queued)
  API->>Worker: send_task → dast queue
  API-->>User: scan_id

  loop Progress
    Worker->>DB: Update findings & events
    Worker->>Redis: LPUSH ws:events:scan_id
    User->>API: WS /ws/scan/scan_id
    API-->>User: Live JSON events
  end
```

### Running Locally with Docker Compose

```bash
git clone https://github.com/your-repo/Major_project.git
cd Major_project/SecureWithAI/backend/compose

# Copy and configure your environment file
cp .env.example .env
# Edit .env with your keys

# Start the full stack
docker compose up
```

| Service | URL |
|---|---|
| **App (via Nginx)** | http://localhost:99 |
| **API (direct)** | http://localhost:9997 |
| **Vite Frontend (direct)** | http://localhost:9998 |
| **Celery Flower** | http://localhost:9999 |
| **API Docs (Swagger)** | http://localhost:9997/api/v1/docs |

### Environment Variables

#### Backend (`.env`)

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://user:pass@postgres:5432/sentinel
REDIS_URL=redis://redis:6379/0
ZAP_URL=http://zap:8090
ZAP_API_KEY=your-zap-key
JWT_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:99,http://localhost:9998
UPLOAD_DIR=/app/uploads
REPORTS_DIR=/app/reports
```

#### Frontend (`.env`)

```env
VITE_API_URL=http://localhost:99
VITE_PROXY_TARGET=http://localhost:9997
VITE_WS_URL=ws://localhost:9997
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id
```

---

## Project Structure

```
Major_project/
├── sentinel-cli/               # Terminal CLI tool
│   ├── src/
│   │   ├── attack/             # Vulnerability scanner modules
│   │   ├── intelligence/       # AI engine & models
│   │   ├── patch/              # AI patch generation
│   │   ├── cli/                # Interactive shell
│   │   ├── plugins/            # Built-in plugins (Nuclei, SSL, etc.)
│   │   ├── config/             # Settings & scan storage
│   │   └── main.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── package.json            # NPM distribution wrapper
│   ├── requirements.txt
│   ├── NPM-INSTALL-GUIDE.md
│   └── DOCKER-INSTALL-GUIDE.md
│
└── SecureWithAI/               # Full-stack web platform
    ├── frontend/               # React + Vite + TypeScript SPA
    │   └── src/
    │       ├── pages/          # marketing/ and app/
    │       ├── components/     # pre_login/, post_login/, shared/
    │       └── lib/            # API client, auth helpers
    └── backend/
        ├── api/                # FastAPI application
        │   ├── api/v1/         # Route handlers
        │   ├── models/         # SQLAlchemy models
        │   ├── workers/        # Celery tasks
        │   └── packages/       # Scanner, AI, Reports packages
        ├── compose/            # docker-compose.yml
        ├── gateway/            # Nginx config
        └── scripts/            # Setup & seed scripts
```

---

## Requirements

### Sentinel CLI

| Requirement | Version | Required |
|---|---|---|
| Python | 3.9+ | ✅ |
| Node.js | 16+ | ✅ |
| pip | Latest | ✅ |
| OpenRouter API Key | — | ✅ |
| Java 11 | For ZAP only | ⚠️ Optional |
| Docker | For Docker mode | ⚠️ Optional |

### Sentinel Web

| Requirement | Version | Required |
|---|---|---|
| Docker + Docker Compose | Latest | ✅ |
| PostgreSQL | 15 | ✅ (via Docker) |
| Redis | Latest | ✅ (via Docker) |
| OWASP ZAP | 2.15+ | ✅ (via Docker) |
| Google OAuth Client ID | — | ⚠️ Optional |
| OpenRouter API Key | — | ✅ For AI features |

---

## Contributing

Contributions are welcome! Here is how to get started:

1.  **Fork** the repository
2.  Create a feature branch: `git checkout -b feature/my-feature`
3.  Make your changes and add tests where applicable
4.  Commit with a clear message: `git commit -m "feat: add my feature"`
5.  Push: `git push origin feature/my-feature`
6.  Open a **Pull Request** with a description of what you changed and why

### Code Style
- **Python**: PEP8, type hints preferred
- **TypeScript**: strict mode, no `any`
- Keep AI model references centralized in `src/intelligence/models.py`

---

## Ethics & Legal

> ⚠️ **Sentinel is an ethical security tool.**

By using this software, you confirm that:

- You **own** the target systems, OR
- You have **explicit written permission** to test them.

**Unauthorized scanning is illegal** and may result in criminal charges under the Computer Fraud and Abuse Act (CFAA), the UK Computer Misuse Act, and equivalent laws worldwide.

The authors of Sentinel accept **no liability** for misuse of this tool.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for the security community.**

*Sentinel — Because your applications deserve better than "probably fine."*

</div>
