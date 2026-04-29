# ShieldSentinel Project Design Documentation

This document contains the architectural and design specifications for **ShieldSentinel**, the full-stack web dashboard component of the Sentinel Security Suite.

---

## 4.1 Architecture Diagram

ShieldSentinel uses a distributed microservices-inspired architecture managed by Docker Compose. It separates high-traffic API handling from long-running security scanning tasks.

```mermaid
graph TB
    subgraph Client_Layer [Client Layer]
        SPA[React 18 / Vite SPA]
        IDE[In-Browser IDE - Monaco]
    end

    subgraph Edge_Gateway [Edge Gateway]
        NGINX[Nginx Gateway :99]
    end

    subgraph API_Service [API Service]
        FastAPI[FastAPI Backend :9997]
        Auth[JWT / OAuth Handler]
        WS[WebSocket Manager]
    end

    subgraph Task_Processing [Task Processing]
        Redis[(Redis Message Broker)]
        WorkerD[Celery Worker: DAST]
        WorkerS[Celery Worker: SAST]
        WorkerA[Celery Worker: AI/Reports]
        Beat[Celery Beat: Scheduler]
    end

    subgraph Persistence_Layer [Persistence Layer]
        DB[(PostgreSQL 15)]
        Disk[Local Reports / Uploads]
    end

    subgraph Security_Tools [Security & AI Tools]
        ZAP[OWASP ZAP]
        Nuclei[Nuclei Scanner]
        AI[OpenRouter AI]
    end

    SPA --> NGINX
    NGINX --> SPA
    NGINX --> FastAPI
    FastAPI --> DB
    FastAPI --> Redis
    FastAPI --> Auth
    Redis --> WorkerD
    Redis --> WorkerS
    Redis --> WorkerA
    WorkerD --> ZAP
    WorkerD --> Nuclei
    WorkerA --> AI
    WorkerD --> DB
    WorkerS --> DB
    WS -.->|Live Updates| SPA
    Beat --> Redis
```

---

## 4.2 UML Diagrams

### Use Case Diagram

Describes how different actors (Security Admin, Developer) interact with the web platform.

```mermaid
graph TD
    Admin((Security Admin))
    Dev((Developer))
    
    subgraph Web_Dashboard
        UC1(Configure Project/Asset)
        UC2(Trigger DAST/SAST Scan)
        UC3(Schedule Recurring Scan)
        UC4(Review Vulnerabilities)
        UC5(Fix Code via AI IDE)
        UC6(Export PDF Report)
        UC7(Manage Team & API Keys)
    end

    Admin --- UC1
    Admin --- UC2
    Admin --- UC3
    Admin --- UC7
    
    Dev --- UC2
    Dev --- UC4
    Dev --- UC5
    Dev --- UC6
    
    UC2 -.->|include| UC4
    UC5 -.->|extend| UC4
```

### Class Diagram (Backend Architecture)

Focuses on the FastAPI application structure and data models.

```mermaid
classDiagram
    class User {
        +id: UUID
        +email: String
        +hashed_password: String
        +is_active: Boolean
    }

    class Project {
        +id: UUID
        +name: String
        +target_url: String
        +owner_id: UUID
    }

    class Scan {
        +id: UUID
        +status: Enum
        +type: String
        +started_at: DateTime
        +project_id: UUID
    }

    class Finding {
        +id: UUID
        +vuln_type: String
        +severity: Enum
        +description: Text
        +scan_id: UUID
    }

    class ScannerService {
        +trigger_dast_task(scan_id)
        +trigger_sast_task(scan_id)
        +get_zap_client()
    }

    class AIService {
        +generate_summary(findings)
        +generate_code_fix(code_snippet)
    }

    User "1" --> "*" Project : owns
    Project "1" --> "*" Scan : contains
    Scan "1" --> "*" Finding : identifies
    ScannerService ..> Scan : updates
    AIService ..> Finding : analyzes
```

### Sequence Diagram: Web Scan Pipeline

Visualizes the lifecycle of a scan from request to UI update.

```mermaid
sequenceDiagram
    participant User as React Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant R as Redis/Celery
    participant W as Worker (DAST)
    participant WS as WebSocket

    User->>API: POST /api/v1/scans (target_url)
    API->>DB: Create Scan entry (status=QUEUED)
    API->>R: Push task to 'dast' queue
    API-->>User: 201 Created (scan_id)
    
    W->>R: Pop task
    W->>DB: Update status (RUNNING)
    W->>WS: Broadcast {status: 'running'}
    
    W->>W: Execute ZAP/Nuclei
    W->>DB: Insert Findings
    W->>WS: Broadcast {finding: 'SQLi detected'}
    
    W->>DB: Update status (COMPLETED)
    W->>WS: Broadcast {status: 'done'}
    User->>API: GET /api/v1/scans/{id}/findings
    API-->>User: Final Findings JSON
```

### Activity Diagram: Scheduled Scan Workflow

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> BeatTrigger: Cron Schedule Match
    BeatTrigger --> TaskQueued: Push to Redis
    TaskQueued --> WorkerPickup: Worker Available
    WorkerPickup --> PreScanCheck: Validate Target
    PreScanCheck --> ActiveScanning: ZAP/SAST
    ActiveScanning --> AI_Summarization: Generate KPI
    AI_Summarization --> Notification: Send Email/Alert
    Notification --> Idle
```

---

## 4.3 Database Design

ShieldSentinel uses a Relational Database (PostgreSQL) for structured data and Redis for ephemeral state/messaging.

### ER Diagram

```mermaid
erDiagram
    USERS ||--o{ PROJECTS : manages
    PROJECTS ||--o{ SCANS : history
    PROJECTS ||--o{ SCHEDULES : auto-run
    SCANS ||--o{ FINDINGS : results
    SCANS ||--|| REPORTS : generates
    
    USERS {
        uuid id PK
        string email
        string full_name
        string oauth_id
    }
    PROJECTS {
        uuid id PK
        string name
        string target_url
        string repository_url
        uuid user_id FK
    }
    SCANS {
        uuid id PK
        enum status
        string scan_type
        timestamp started_at
        uuid project_id FK
    }
    FINDINGS {
        uuid id PK
        string severity
        string vuln_type
        text description
        text remediation
        uuid scan_id FK
    }
```

### Table Structure (SQL Schema)

#### 1. `users`
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY |
| `email` | String | UNIQUE, NOT NULL |
| `hashed_password` | String | NULL (if OAuth) |
| `created_at` | Timestamp | DEFAULT NOW() |

#### 2. `scans`
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY |
| `project_id` | UUID | FOREIGN KEY -> projects.id |
| `status` | String | QUEUED, RUNNING, COMPLETED, FAILED |
| `risk_score` | Integer | 0 - 100 |

#### 3. `findings`
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY |
| `scan_id` | UUID | FOREIGN KEY -> scans.id |
| `severity` | Enum | Critical, High, Medium, Low |
| `cve_id` | String | NULL |

---

### Data Dictionary

| Term | Definition |
| :--- | :--- |
| **Worker (Celery)** | A dedicated process for running resource-intensive scans without blocking the API. |
| **Beat** | The scheduler service that triggers tasks at specific intervals (Cron). |
| **Risk Score** | A calculated value based on the count and severity of findings in a scan. |
| **SAST** | Static Application Security Testing (Scanning source code/ZIP files). |
| **DAST** | Dynamic Application Security Testing (Scanning live running URLs). |
| **In-Browser IDE** | A Monaco-based code editor integrated with AI to fix vulnerabilities directly. |
