# Sentinel Project Design Documentation

This document contains the architectural and design specifications for **Sentinel**, an AI-powered security scanning and remediation platform.

---

## 4.1 Architecture Diagram

Sentinel follows a modular CLI-first architecture with AI orchestration. It integrates external security tools (ZAP) with cloud-based or local AI models to provide actionable security intelligence.

```mermaid
graph TB
    subgraph User Interface
        CLI[Sentinel CLI - Typer/Rich]
        Shell[Interactive Shell]
    end

    subgraph Core Engine
        Main[Main Controller]
        CM[Config Manager]
        PM[Plugin Manager]
    end

    subgraph Intelligence Layer
        AB[Attack Brain - AI Orchestrator]
        PE[Patch Engine]
        CE[Chat/Compare Engine]
    end

    subgraph External Tools
        ZAP[OWASP ZAP Daemon]
        Ollama[Ollama Local AI]
        OR[OpenRouter Cloud AI]
    end

    subgraph Storage [Local Filesystem]
        FS[~/.sentinel/]
        Scans[Scans Data - JSON]
        Logs[System Logs]
        Plugins[Skill Plugins]
    end

    CLI --> Main
    Shell --> Main
    Main --> CM
    Main --> PM
    Main --> AB
    AB --> ZAP
    AB --> OR
    AB --> Ollama
    Main --> PE
    PE --> OR
    Main --> CE
    CM --> FS
    Main --> Scans
    PM --> Plugins
```

---

## 4.2 UML Diagrams

### Use Case Diagram

Describes the primary interactions between the Security Analyst and the Sentinel system.

```mermaid
graph TD
    User((Security Analyst))
    
    subgraph Sentinel_System
        UC1(Run Vulnerability Scan)
        UC2(Generate AI Patches)
        UC3(Chat with Security AI)
        UC4(Manage Plugins)
        UC5(View Scan History)
        UC6(Configure System)
    end

    User --- UC1
    User --- UC2
    User --- UC3
    User --- UC4
    User --- UC5
    User --- UC6
    
    UC1 -.->|include| UC5
    UC2 -.->|extend| UC1
```

### Class Diagram

Key components and their relationships within the Sentinel CLI.

```mermaid
classDiagram
    class ConfigManager {
        +SENTINEL_HOME: Path
        +get(key, fallback)
        +set(key, value)
        +new_scan_dir(target_url) Path
        +list_scans() List
    }

    class PluginManager {
        +PLUGINS_DIR: Path
        +install(name)
        +run_plugin(name, url)
        +list_plugins()
    }

    class AttackBrain {
        +provider: str
        +attack(url, mode)
        +generate_report()
    }

    class PatchEngine {
        +generate_patches(findings_path)
        +apply_templates()
    }

    class ZAPScanner {
        +ensure_zap_running()
        +start_scan(url)
        +get_results()
    }

    AttackBrain --> ZAPScanner : Orchestrates
    AttackBrain --> ConfigManager : Reads settings
    MainController --> AttackBrain
    MainController --> PatchEngine
    MainController --> PluginManager
```

### Sequence Diagram: Scan Execution Flow

Shows the logic flow when a user initiates a scan.

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Brain as AttackBrain
    participant ZAP as ZAP Scanner
    participant AI as AI Provider (OpenRouter/Ollama)
    participant FS as Local Storage

    User->>CLI: sentinel scan --url <target>
    CLI->>CLI: Validate URL & Ethics
    CLI->>Brain: initiate_attack(target)
    Brain->>ZAP: start_spider_and_scan(target)
    ZAP-->>Brain: Raw Vulnerability Data
    Brain->>AI: analyze_vulnerabilities(raw_data)
    AI-->>Brain: Structured Insights & Severity
    Brain->>FS: save_findings(findings.json)
    Brain->>FS: save_metadata(meta.json)
    Brain-->>CLI: Display Summary Table
    CLI-->>User: Visual Report
```

### Activity Diagram: Vulnerability Remediation Lifecycle

```mermaid
stateDiagram-v2
    [*] --> StartScan
    StartScan --> Crawling
    Crawling --> Scanning
    Scanning --> Analysis: Raw Results Ready
    Analysis --> AI_Processing
    AI_Processing --> FindingsSaved
    FindingsSaved --> UserReview
    UserReview --> PatchGeneration: Request Fixes
    PatchGeneration --> AI_Patching: Context-Aware Generation
    AI_Patching --> Verification: User Tests Patch
    Verification --> [*]
```

---

## 4.3 Database Design

Sentinel uses a **Document-Oriented Filesystem Storage** approach. Each scan is treated as a unique record (folder) containing JSON documents.

### ER Diagram (Logical)

```mermaid
erDiagram
    SCAN ||--o{ FINDING : contains
    SCAN ||--o{ PATCH : generates
    SCAN ||--|| METADATA : describes
    SCAN {
        string scan_id PK
        string target_url
        datetime timestamp
    }
    FINDING {
        string vuln_id PK
        string type
        string severity
        string description
        string evidence
    }
    PATCH {
        string patch_id PK
        string file_path
        string fix_code
        string explanation
    }
    METADATA {
        string version
        string mode
        int total_findings
    }
```

### Table Structure (JSON Schema Representation)

#### 1. `meta.json` (Scan Header)
| Field | Type | Description |
| :--- | :--- | :--- |
| `target` | String | The URL of the scanned application. |
| `scanned_at` | DateTime | ISO timestamp of the scan start. |
| `mode` | String | Scan intensity (fast, deep, stealth). |
| `total_findings`| Integer | Count of identified vulnerabilities. |

#### 2. `findings.json` (Vulnerability Records)
| Field | Type | Description |
| :--- | :--- | :--- |
| `vuln_type` | String | Type of vulnerability (e.g., SQLi, XSS). |
| `severity` | String | Critical, High, Medium, Low, or Informational. |
| `url` | String | The specific endpoint where the flaw was found. |
| `evidence` | String | Raw HTTP request/response or snippet proving the flaw. |
| `remediation` | String | AI-suggested high-level fix. |

#### 3. `patches.json` (Fix Recommendations)
| Field | Type | Description |
| :--- | :--- | :--- |
| `file_context` | String | The source file or code block being patched. |
| `vulnerability` | String | Link to the finding being addressed. |
| `safe_code` | String | The secure version of the code. |
| `explanation` | String | Detailed reasoning for the security fix. |

---

### Data Dictionary

| Term | Definition |
| :--- | :--- |
| **SENTINEL_HOME** | The root directory for all persistent data (~/.sentinel). |
| **Scan ID** | A unique timestamped slug identifying a specific scan session. |
| **Brain** | The AI orchestration layer that handles prompt engineering and response parsing. |
| **Plugin** | A standalone security tool (e.g., Nuclei, Subfinder) integrated into the workflow. |
| **ZAP Daemon** | The background process running OWASP ZAP for dynamic analysis. |
