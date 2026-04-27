# Sentinel Security Suite: Unified Testing Report
**Version:** 1.1.0 | **Project:** Sentinel & ShieldSentinel | **Date:** April 2026

---

## 7.1 Test Plan

### 1. Objective
The objective of this unified test plan is to validate the entire **Sentinel Security Suite**, ensuring the CLI, the Landing Page, and the **ShieldSentinel Web Dashboard** function as a cohesive security ecosystem.

### 2. Scope
The testing scope encompasses:
- **Sentinel CLI**: Native Attack Engine, AI Brain orchestration, and Interactive Shell.
- **Sentinel Web (Landing Page)**: Cyber-Noir UX, responsive design, and interactive visuals.
- **ShieldSentinel (Full-Stack Dashboard)**:
    - **Frontend**: React 18 SPA, Monaco IDE integration, and WebSocket status updates.
    - **Backend**: FastAPI endpoints, JWT authentication, and PostgreSQL data integrity.
    - **Processing**: Celery workers, Redis message brokerage, and scan scheduling (Beat).

### 3. Testing Environment
- **OS**: Windows (Host) / Ubuntu 22.04 (Docker Containers)
- **Tech Stack**: Python 3.10, Node.js 20, React 18, FastAPI, PostgreSQL 15, Redis, Celery.
- **Tools**: `pytest` (Backend/CLI), `Cypress` (Frontend E2E), OWASP ZAP (DAST), Monaco Editor.

---

## 7.2 Test Cases Table

| Test Case ID | Module | Input | Expected Output | Result |
| :--- | :--- | :--- | :--- | :--- |
| **TC-CLI-001** | CLI Core | `sentinel scan --url <target>` | Engine runs 11 parallel checks; findings saved to JSON. | **Pass** |
| **TC-CLI-002** | AI Brain | Raw vulnerability data | AI generates prioritized "Hacker Summary" with remediation. | **Pass** |
| **TC-WEB-001** | Landing Page | User interaction (scroll/click) | Smooth "Cyber-Noir" transitions and cursor glow effects. | **Pass** |
| **TC-SS-001** | SS Auth | User Login (Valid Credentials) | JWT token issued; redirected to Dashboard workspace. | **Pass** |
| **TC-SS-002** | SS Project | Create new project with target URL | Project metadata saved to Postgres; asset listed in UI. | **Pass** |
| **TC-SS-003** | SS Scan | Trigger DAST scan from Dashboard | Celery task queued; status updates to "RUNNING" via WebSocket. | **Pass** |
| **TC-SS-004** | SS IDE | Open Monaco IDE on a finding | Source code loaded with AI-suggested fix overlay. | **Pass** |
| **TC-SS-005** | SS Scheduler | Set recurring scan (Cron) | Celery Beat triggers scan at specified interval automatically. | **Pass** |
| **TC-SS-006** | SS Reporting | "Export PDF" button click | Dynamic PDF generated with project branding and findings. | **Pass** |
| **TC-INT-001** | Integration | CLI scan data upload to SS | CLI results successfully sync with the Web Dashboard DB. | **Pass** |

---

## 7.3 Types of Testing

### 1. Unit Testing
- **CLI**: Testing individual vulnerability check modules in `src/attack/`.
- **Backend (SS)**: Testing FastAPI schemas and utility functions for data validation.
- **Frontend (SS)**: Testing React components for state management and UI rendering.

### 2. Integration Testing
- **Orchestration**: Validating the flow between CLI/Dashboard and OpenRouter AI.
- **Message Broker**: Ensuring Redis correctly routes tasks from FastAPI to Celery workers.
- **Database**: Verifying referential integrity across Users, Projects, and Scans.

### 3. System Testing
- **End-to-End Suite**: Starting a scan via CLI and viewing the real-time progress on the ShieldSentinel Dashboard.
- **Containerization**: Testing the full Docker Compose stack (FastAPI, Postgres, Redis, Workers).

### 4. User Acceptance Testing (UAT)
- **Admin UX**: Validating that security admins can effectively manage teams and team-wide API keys.
- **Developer UX**: Ensuring the In-Browser IDE experience is intuitive for non-security developers to apply patches.
- **Theme Integrity**: Ensuring the "Cyber-Noir" aesthetic is consistent across the landing page, CLI output, and the Dashboard UI.
