# ITOM OPS Analytics & Microsoft Intune Automated Data Sync Strategy

## 1. Executive Summary & Architecture Overview

The IT Operations Management (ITOM) Operations Analytics module relies on high-fidelity, verified telemetry from Microsoft Intune, SolarWinds Orion, and enterprise network infrastructure. To maintain near real-time operational observability without manual intervention or performance degradation, this document defines the production **Automated Data Sync Strategy (M4 / R4)**.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                   AUTOMATED TELEMETRY REFRESH & SYNC PIPELINE                  │
└────────────────────────────────────────────────────────────────────────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
    [Scheduled Cron Trigger]                      [Manual / Event Trigger]
      GitHub Actions Weekly                          Workflow Dispatch /
     (cron: '0 2 * * 1' UTC)                           Cloud Function
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │ 1. INGESTION (MS Graph API)   │
                      │  • OAuth 2.0 Client Creds     │
                      │  • Jittered Exponential Retry │
                      │  • Paginated Stream (25,987)  │
                      └───────────────┬───────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │ 2. ETL & NORMALIZATION ENGINE │
                      │  • Case-Insensitive OEM Norm  │
                      │  • Compliance Breakdown Rate  │
                      │  • Storage GB & Pct Math      │
                      └───────────────┬───────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │ 3. MATHEMATICAL INVARIANT GATE│
                      │  • verify_intune_data.py      │
                      │  • Assert Σ subsets == 25,987 │
                      │  • Zero Tolerance Halt on Err │
                      └───────────────┬───────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
       ┌───────────────────────────┐     ┌───────────────────────────┐
       │ 4A. PERSISTENCE & HOSTING │     │ 4B. CLOUD FIRESTORE SYNC  │
       │  • data/intune_summary.json│     │  • Collection: itom_telemetry
       │  • Sub-10ms CDN Delivery  │     │  • Doc ID: intune_summary │
       │  • Firebase Hosting Deploy│     │  • Batch Device Commits   │
       └───────────────────────────┘     └───────────────────────────┘
```

---

## 2. Ingestion Schedule & Triggers

### 2.1 Scheduled Workflow (`.github/workflows/intune_telemetry_sync.yml`)
- **Cron Schedule**: `0 2 * * 1` (Every Monday at 02:00 UTC / 07:30 IST).
- **Rationale**: Off-peak telemetry extraction prevents throttling against Microsoft Graph API tenant rate limits while ensuring weekly executive reporting metrics are primed before standard business hours.
- **Concurrency Control**: Enforces single-instance execution (`concurrency.group: intune-telemetry-sync`) with `cancel-in-progress: true` to prevent concurrent write contention.

### 2.2 Manual Trigger (`workflow_dispatch`)
- Operators can trigger an immediate on-demand telemetry sync with parameterized options:
  - `force_live_fetch` (boolean): Forces full Microsoft Graph API query.
  - `skip_firestore` (boolean): Bypasses cloud database writes for local verification.

### 2.3 Cloud Function / Webhook Trigger (Alternative Extension)
- A Google Cloud Function / AWS Lambda endpoint listening to Azure Event Grid / Webhooks for delta device enrollment events can execute `src/sync/run_sync.py` via containerized serverless execution.

---

## 3. Microsoft Graph API Ingestion Pipeline

### 3.1 Authentication & Token Lifecycle (`src/sync/graph_client.py`)
- **Protocol**: OAuth 2.0 Client Credentials Grant (`client_credentials`).
- **Endpoint**: `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token`
- **Scope**: `https://graph.microsoft.com/.default`
- **Permissions**: Application permission `DeviceManagementManagedDevices.Read.All` (Principle of Least Privilege).
- **Token Caching**: `GraphClient` caches the bearer token and refreshes it proactively 60 seconds prior to expiration (`expires_in - 60s`).

### 3.2 Paginated Data Streaming
- Endpoint: `https://graph.microsoft.com/v1.0/deviceManagement/managedDevices`
- Default page size: `$top=1000`
- Extracted Fields:
  - `id`, `deviceName`, `operatingSystem`, `osVersion`, `complianceState`
  - `userPrincipalName`, `model`, `manufacturer`, `serialNumber`, `lastSyncDateTime`
  - `totalStorageSpaceInBytes`, `freeStorageSpaceInBytes`
- Pagination follows `@odata.nextLink` until all 25,987+ devices are ingested.

### 3.3 Rate Limiting & Resilience Strategy
- **429 Too Many Requests**: Reads `Retry-After` header and applies exponential backoff with randomized jitter ($\text{delay} = 2^{\text{attempt}} + \text{uniform}(0, 1)$).
- **503 Service Unavailable / 504 Gateway Timeout**: Maximum 5 retry attempts before aborting and raising an operational alert.

---

## 4. Normalization & Transformation Engine (`src/sync/payload_generator.py`)

### 4.1 Case-Insensitive OEM Normalization
Raw device metadata from diverse firmware versions produces inconsistent manufacturer strings. The aggregation engine normalizes all records:

| Raw Input Variations | Standardized Output | Fleet Proportion (25,987 Records) |
|---|---|---|
| `"Dell Inc."`, `"DELL"`, `"dell"` | **`Dell`** | 15,716 (60.48%) |
| `"HP"`, `"Hewlett-Packard"`, `"hp inc."` | **`HP`** | 8,610 (33.13%) |
| `"LENOVO"`, `"Lenovo"`, `"lenovo"` | **`Lenovo`** | 959 (3.69%) |
| `"Apple"`, `"APPLE"`, `"Apple Inc."` | **`Apple`** | 604 (2.32%) |
| Others (Microsoft, ASUS, Acer, OEM) | **`Other`** | 98 (0.38%) |

### 4.2 Mathematical Invariants Calculation
1. **Fleet Compliance Rate**:
   $$\text{Rate} = \frac{21589 \text{ (Compliant)}}{25987 \text{ (Total)}} \times 100 = 83.08\%$$
2. **Fleet Disk Utilization**:
   $$\text{Storage Used Pct} = \frac{10732842.82 \text{ GB (Total)} - 6724196.48 \text{ GB (Free)}}{10732842.82 \text{ GB (Total)}} \times 100 \approx 37.35\% \rightarrow 37.4\%$$

---

## 5. Mathematical Invariant Verification Gate (`tests/verify_intune_data.py`)

Prior to deploying or publishing any synchronized payload, the automated pipeline runs the invariant test gate:

```bash
python tests/verify_intune_data.py
```

### Asserted Constraints:
1. $\sum \text{Compliance States} == 25,987$
2. $\sum \text{Operating Systems} == 25,987$
3. $\sum \text{Manufacturers} == 25,987$
4. $\text{Storage reporting devices} == 25,937$
5. $\text{Compliant count} == 21,589$
6. $\text{Non-compliant count} == 3,422$
7. $\text{ConfigManager count} == 935$
8. $\text{Summary reconciliation discrepancies} == 0$

*If any assertion fails, the sync process exits with code 1, immediately halting commit, deployment, and cloud database persistence.*

---

## 6. Persistence & Cloud Synchronization

### 6.1 Google Cloud Firestore (`src/sync/firestore_sync.py`)
- **Collection**: `itom_telemetry`
- **Document ID**: `intune_summary`
- **Sync Metadata**: Automatically records `synced_at`, `status`, and `offline_mode` indicator.
- **Batch Processing**: Commits individual device records to `intune_devices` in batches of 500 documents (Firestore atomic transaction limit).
- **Offline / Air-Gapped Fallback**: When running in local environments or without GCP credentials, `FirestoreSyncService` logs the payload and saves local cached payloads without failing the process.

### 6.2 Precomputed Static Payload (`data/intune_summary.json`)
- Serving precomputed summary JSON from CDN / Firebase Hosting allows sub-10ms browser startup without running real-time database queries on high-traffic dashboards.

---

## 7. Security Model & Secrets Management

1. **Zero Hardcoded Secrets**: Secrets (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `FIREBASE_PROJECT_ID`, `GCP_SA_KEY`) are stored exclusively in GitHub Actions Encrypted Secrets or Google Secret Manager.
2. **Access Control**: Service accounts utilize least-privilege IAM roles (`roles/datastore.user` for Firestore, read-only Graph application permissions).
3. **Data Minimization & Sanitation**: Telemetry payloads exclude PII beyond standard corporate UPN identifiers.

---

## 8. Failover & Operational Runbook

### Scenario 1: Microsoft Graph API Ingestion Failure (HTTP 401 / 403 / 5xx)
1. Ingestion logs error and halts.
2. CI/CD sends notification to SRE Slack/Teams webhook.
3. Dashboard continues serving previous verified `data/intune_summary.json` payload without downtime.

### Scenario 2: Mathematical Invariant Failure
1. `tests/verify_intune_data.py` raises `AssertionError`.
2. Pipeline exits with code 1.
3. Incomplete or corrupted data is rejected before writing to production or Firestore.

### Manual CLI Execution:
```bash
# Full sync pipeline (using existing raw dataset)
python scripts/run_sync.py --skip-fetch

# Full sync with live Microsoft Graph ingestion
python scripts/run_sync.py --fetch-live

# Invariant audit verification
python tests/verify_intune_data.py

# Complete E2E test suite execution
python tests/run_e2e_tests.py --verbose
```
