# Sentinel Security — Docker Install Guide

> **AI-Powered Ethical Hacking & Patch Engine**  
> `sentinel-security:latest` — Batteries Included, Zero Setup

---

## Why Use Docker?

The Docker version of Sentinel is the most powerful way to run it. Unlike the NPM version which requires Python to be installed, Docker bundles **everything** inside a single portable container:

| What's Included | Version |
|---|---|
| Ubuntu Linux | 22.04 LTS |
| Python | 3.10 |
| Java (for ZAP) | OpenJDK 11 |
| OWASP ZAP | 2.15.0 |
| Nuclei | 3.3.0 |
| Subfinder | 2.6.6 |
| Node.js | 20.x |
| Sentinel CLI | 0.2.0 |

**Zero configuration. Just run and hack.**

---

## Prerequisites

You only need **one thing** installed on your computer:

- **Docker Desktop**: Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

That's it. No Python. No Java. No ZAP. Docker handles everything.

---

## Option A: Pull from Docker Hub (Recommended)

If the image has been published to Docker Hub, anyone can pull and run it with a single command:

```bash
docker pull yourusername/sentinel-security:latest
```

Then run it:
```bash
docker run -it -e OPENROUTER_API_KEY=sk-or-your-key yourusername/sentinel-security
```

---

## Option B: Build Locally from Source

If you have the source code (this repository), you can build the image yourself.

### Step 1 — Clone the repository
```bash
git clone https://github.com/your-repo/sentinel-cli.git
cd sentinel-cli
```

### Step 2 — Build the Docker Image
```bash
docker build -t sentinel-security:latest .
```
> ⏱️ The first build takes **5–10 minutes** as it downloads and installs ZAP, Nuclei, and Python dependencies. Subsequent builds are instant due to Docker layer caching.

### Step 3 — Verify the Image was created
Open Docker Desktop → **Images** tab. You should see `sentinel-security` listed.

Or verify via command line:
```bash
docker images sentinel-security
```

---

## Running Sentinel

### Basic Run (Recommended for first-time users)
```bash
docker run -it -e OPENROUTER_API_KEY=sk-or-your-key sentinel-security
```

You will see:
1.  ZAP daemon starting in the background.
2.  The Sentinel banner appearing.
3.  An interactive shell where you can type commands.

---

### Persist your Scan History (Recommended)

By default, all scan data is lost when the container stops. To save your scans to your local computer, use a **volume mount**:

#### Windows (PowerShell)
```powershell
docker run -it `
  -v ${HOME}/.sentinel/scans:/root/.sentinel/scans `
  -e OPENROUTER_API_KEY=sk-or-your-key `
  sentinel-security
```

#### macOS / Linux
```bash
docker run -it \
  -v ~/.sentinel/scans:/root/.sentinel/scans \
  -e OPENROUTER_API_KEY=sk-or-your-key \
  sentinel-security
```

Your scan reports will now be saved at `~/.sentinel/scans/` on your actual computer.

---

### Use with a `.env` File (Most Convenient)

Instead of typing your API key every time, create a `.env` file in the current directory:

```
OPENROUTER_API_KEY=sk-or-your-key-here
```

Then pass it to Docker:
```bash
docker run -it --env-file .env sentinel-security
```

> ⚠️ **Never commit your `.env` file to Git!** Make sure it's in your `.gitignore`.

---

## Quick Start Commands

Once you're inside the Sentinel shell:

```bash
# Run a full security scan
sentinel scan --url https://example.com

# Run a fast native scan only
sentinel scan --url https://example.com --mode fast

# Generate AI patches for the last scan
sentinel patches

# Chat with AI about your scan
sentinel chat

# Compare two scans
sentinel compare <scan-id-1> <scan-id-2>

# View scan history
sentinel history

# Check system health
sentinel doctor
```

---

## Docker Desktop Guide

### Images Tab
- Go to Docker Desktop → **Images**
- You will see `sentinel-security` listed here
- This is your "blueprint" — it's not a running process yet

### Containers Tab
- Containers only appear here when they are **actively running**
- Run the `docker run` command above to start one
- You'll see a new row appear in real-time as it starts
- When you type `exit` in Sentinel, the container will stop and move to "Exited" state

### Starting an Exited Container Again
If you have a stopped container you want to restart:
```bash
# List all containers (including stopped)
docker ps -a

# Restart a specific container
docker start -i <container-id>
```

---

## Scan Mode Reference

| Mode | Command | Speed | Description |
|---|---|---|---|
| Fast | `--mode fast` | ~60–90 sec | Native Python engine only |
| Deep | `--mode deep` | ~10 min | Native + ZAP + Nikto |

In Docker, the **deep mode** works best since ZAP is already pre-installed and running!

---

## Publishing Your Image to Docker Hub

Once you're happy with your build, share it with the world:

### Step 1 — Create a Docker Hub account
Sign up at [hub.docker.com](https://hub.docker.com)

### Step 2 — Login
```bash
docker login
```

### Step 3 — Tag your image with your username
```bash
docker tag sentinel-security:latest yourusername/sentinel-security:latest
```

### Step 4 — Push to Docker Hub
```bash
docker push yourusername/sentinel-security:latest
```

**Anyone can now run your tool with:**
```bash
docker run -it -e OPENROUTER_API_KEY=your-key yourusername/sentinel-security
```

---

## Troubleshooting

### ❌ `docker: command not found`
Docker Desktop is not installed. Download it from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop).

---

### ❌ `Cannot connect to the Docker daemon`
Docker Desktop is not running. Open Docker Desktop from your Start Menu and wait for it to fully load (the whale icon in the system tray should stop animating).

---

### ❌ `Error: Missing OPENROUTER_API_KEY`
You forgot to pass your API key to the container. Use one of these methods:

```bash
# Inline:
docker run -it -e OPENROUTER_API_KEY=sk-or-your-key sentinel-security

# Via .env file:
docker run -it --env-file .env sentinel-security
```

---

### ❌ `No such image: sentinel-security`
You haven't built the image yet. Run:
```bash
docker build -t sentinel-security:latest .
```

---

### ❌ ZAP takes a long time to start
This is normal on first run. ZAP (Java-based) needs 20–40 seconds to initialize. Sentinel will automatically wait for it before starting the CLI.

---

### ❌ Build fails with 404 on ZAP download
The ZAP download mirror may have changed. Check the latest release at [github.com/zaproxy/zap-archive](https://github.com/zaproxy/zap-archive/releases) and update the `ZAP_VERSION` variable in the `Dockerfile`.

---

## System Requirements

| Component | Minimum |
|---|---|
| RAM | 4 GB (8 GB recommended for ZAP deep scans) |
| Disk Space | 3 GB free (for the Docker image) |
| OS | Windows 10/11, macOS 12+, Ubuntu 20.04+ |
| Docker Desktop | Latest version |

---

*Sentinel Security is an ethical hacking tool. Only scan targets you own or have explicit written permission to test. Unauthorized scanning is illegal.*
