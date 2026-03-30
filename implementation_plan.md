# Integrate Advanced Attack Phases (Phase 3 & Phase 4)

This plan outlines the integration of Phase 3 (Authentication Attacks) and Phase 4 (Authenticated Attacks) into the Sentinel AI CLI. This will upgrade the tool from basic reconnaissance and injection testing to finding high-value business logic flaws like IDOR and Auth bypasses.

## User Review Required

> [!IMPORTANT]
> **Authentication state is required for Phase 4.** To properly test IDOR and privilege escalation, the scanner needs to know how to log in, or it must be provided with valid session tokens. We need to decide how the user provides this information.

## Proposed Changes

### 1. Attack Modules (`src/attack/`)

We will create two new independent attack modules that follow the existing `zap_scanner.py` and `nikto_scanner.py` patterns. They will output standard JSON finding objects.

#### [NEW] `src/attack/auth_scanner.py`
This module will handle **Phase 3 — Authentication Attacks**.
- **Capabilities**: 
  - Login page detection (spidering or common paths like `/login`, `/api/auth`).
  - Auth SQLi (e.g., testing `' OR '1'='1`).
  - JWT Weakness Checks (checking for `none` algorithm, trivially weak secrets).
  - User enumeration (analyzing differing error messages for valid/invalid users).
- **Interface**: `def run_auth_scan(target_url, console=None)`

#### [NEW] `src/attack/idor_scanner.py`
This module will handle **Phase 4 — Authenticated Attacks**.
- **Capabilities**:
  - Identifying endpoints with numeric IDs or UUIDs (e.g., `/api/users/1`).
  - Parameter tampering (swapping `1` for `2`).
  - Mass assignment checks (injecting `{"role": "admin"}` into PATCH/PUT bodies).
- **Interface**: `def run_idor_scan(target_url, headers=None, console=None)`

### 2. Brain Orchestrator (`src/intelligence/brain.py`)

We need to update the `AttackBrain` to be aware of these new offensive capabilities.

#### [MODIFY] `src/intelligence/brain.py`
- **`HACKER_PROMPT`**: Update the prompt to explain when the AI should trigger the auth and IDOR scans (e.g., "If exposure or spidering finds a login endpoint, call `run_auth_scan`").
- **`TOOL_SCHEMAS`**: Add configurations for `run_auth_scan` and `run_idor_scan` so Groq knows the parameters and descriptions.
- **`TOOL_LABELS`**: Map the new tools to UI-friendly output labels.
- **`execute_tool`**: Import and link the new tool names to their corresponding functions.

### 3. CLI Input (`src/main.py` & `src/cli/app.py`)

#### [MODIFY] `src/main.py`
- Add CLI arguments for handling authentication. For example, `--auth-header "Authorization: Bearer <token>"` or `--username` & `--password`.
- Pass these credentials down so `run_idor_scan` can test endpoints authentically.

---

## Open Questions

> [!WARNING]
> Please provide feedback on the following implementation details:

1. **Handling Credentials**: For Phase 4 (IDOR/PrivEsc), how should the user supply credentials? Should we add `--token` and `--cookie` flags to the CLI, or perhaps a configuration file?
2. **Test Users**: To accurately test IDOR, we typically need *two* separate user accounts (User A tries to access User B's data). Should Sentinel require two sets of headers for maximum effectiveness?
3. **Brute Forcing Policy**: You mentioned brute forcing in Phase 3. Real brute forcing is slow and noisy. Should we stick to testing a very small dictionary (e.g., `admin/admin`, `test/test`), or do you want a heavier brute force capability?

## Verification Plan

### Automated Tests
- Build simple local unit tests for `auth_scanner.py` mocking a login response.
- Build simple local unit tests for `idor_scanner.py` mocking ID swapping.

### Manual Verification
- Point Sentinel at an intentionally vulnerable web app (e.g., OWASP Juice Shop or a locally spun-up vulnerable API).
- Verify the terminal UI correctly shows the Groq Brain deciding to use "Auth Scan" and "IDOR Scan".
- Check that the final output JSON contains `High` severity findings for IDOR and Auth Bypasses when discovered.
