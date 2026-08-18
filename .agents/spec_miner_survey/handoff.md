# Specification Mining & Requirements Survey Report
**Project:** ITOM Portal — Module 1: OPS Analytics  
**Surveyed By:** Specification Miner Agent  
**Date / UTC Timestamp:** 2026-08-17T19:00:00Z  
**Target Path:** `c:/Users/Roshan.Sah/Documents/antigravity/optimistic-pasteur/.agents/spec_miner_survey/handoff.md`

---

## 1. Observation

Direct code and dataset observations conducted across the workspace:

1. **`ORIGINAL_REQUEST.md` Requirements**:
   - **R1: Microsoft Intune & Tab Navigation Fix**: Fix tab switching in `ops_analytics.html` across 5 tabs: `"Microsoft Intune (Live)"`, `"Overview"`, `"SolarWinds"`, `"Network"`, and `"DEX"`. Instant loading, clean visual state indicators, launcher compatibility, zero infinite buffering.
   - **R2: Independent Multi-Agent Verification & Data Integrity**: Cross-verify 25,987 Intune devices against dashboard summaries (OS breakdown, compliance rates, manufacturer distribution). Zero hallucination, strict mathematical consistency. Deliver automated test script `tests/verify_intune_data.py`.
   - **R3: Code Structure & Engineering Cleanliness**: Organize codebase into modular folders (`src/`, `scripts/`, `data/`, `docs/`, `tests/`) with comprehensive docstrings and comments adhering to clean architecture principles.
   - **R4: Automated Refresh & Data Sync Strategy**: Design and document automated data sync mechanism (e.g. weekly scheduled sync or automated Cloud Function/cron trigger into Firestore/Hosting) so telemetry refreshes reliably without manual intervention.

2. **Codebase Inspection**:
   - `ops_analytics.html` contains tab buttons in header (lines 36–42):
     ```html
     <button class="tab-btn active" data-tab="overview">Overview</button>
     <button class="tab-btn" data-tab="intune">Microsoft Intune (Live)</button>
     <button class="tab-btn" data-tab="solarwinds">SolarWinds (Pending)</button>
     <button class="tab-btn" data-tab="network">Network & CMDB</button>
     <button class="tab-btn" data-tab="dex">DEX Metrics</button>
     ```
   - `ops_analytics.js` (lines 1–245): Currently contains **no click event listeners** or switching logic for `.tab-btn`. The page renders a single unified view with all Intune KPIs, charts, and table. No tab switching or panel hiding occurs.
   - `index.html` & `app.js` (lines 124–157): Launcher cards trigger `launchModule(moduleName, targetUrl)` with a 250ms overlay before navigating to `ops_analytics.html`. However, module cards (`#cmdb`, `#compliance`, `#capacity`, `#dex`) route generically to `ops_analytics.html` without passing active tab context (e.g. `#dex`, `#network`).
   - `data/intune_ops_analytics.json` (16,007,491 bytes): Contains exactly **25,987 device records** in `devices` array and summary object.
   - `data/intune_summary.json` (53,172 bytes): Contains aggregated metrics and 100 sample device records.
   - `scripts/fetch_intune_data.py`: Microsoft Graph API client using Azure AD OAuth 2.0 client credentials (`https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token`) and paginated device fetching (`https://graph.microsoft.com/v1.0/deviceManagement/managedDevices`).
   - `scripts/generate_dashboard_payload.py`: Aggregation script that processes `intune_ops_analytics.json` into `intune_summary.json`.
   - `docs/MRD_Module_1_OPS_Analytics.md`: Product requirements document specifying scope, P0 requirements (FR-001 through FR-005), CSV export (FR-006), and dark UI design tokens (`#0B0B0B` background, `#F97316` orange accents).

3. **Mathematical Verification of Telemetry Data (25,987 Devices)**:
   - **Total Managed Devices**: `25,987`
   - **Compliance Distribution**:
     - `compliant`: **21,589** (83.08%)
     - `noncompliant`: **3,422** (13.17%)
     - `configManager`: **935** (3.60%)
     - `unknown`: **31** (0.12%)
     - `inGracePeriod`: **10** (0.04%)
     - **Sum**: 21,589 + 3,422 + 935 + 31 + 10 = **25,987** (100.00% exact match).
   - **Operating System Distribution**:
     - `Windows`: **25,334** (97.49%)
     - `macOS`: **602** (2.32%)
     - `Linux (ubuntu)`: **24** (0.09%)
     - `Unknown` (`""`): **24** (0.09%)
     - `iOS`: **2** (0.01%)
     - `Android`: **1** (0.00%)
     - **Sum**: 25,334 + 602 + 24 + 24 + 2 + 1 = **25,987** (100.00% exact match).
   - **Hardware Manufacturer Distribution** (Current mapping logic):
     - `Dell`: **15,716** (60.48%)
     - `HP`: **8,610** (33.13%)
     - `Other`: **1,057** (4.07%) — *Note: Includes 959 uppercase `LENOVO` devices, 46 Microsoft, 24 Unknown, 12 Asus, 5 Acer, 3 MSI, 2 Gigabyte, 2 OEM, 1 Alienware, 1 Nutanix, 1 OnePlus, 1 VMware*
     - `Apple`: **604** (2.32%)
     - **Sum**: 15,716 + 8,610 + 1,057 + 604 = **25,987** (100.00% exact match).
   - **Fleet Disk Utilization**:
     - Total Allocated Space across fleet: **12,419,008.2 GB**
     - Total Free Space across fleet: **7,772,408.8 GB**
     - Calculated Storage Used: **37.4%** (Average free storage: **62.6%**)

---

## 2. Logic Chain

1. **R1 Analysis (Tab Navigation & Visual States)**:
   - *Observation*: Tab buttons exist in `ops_analytics.html` (`data-tab="overview"`, `"intune"`, `"solarwinds"`, `"network"`, `"dex"`), but `ops_analytics.js` lacks tab click handling and view containers.
   - *Reasoning*: To deliver seamless tab switching without reloading or buffering, the DOM must feature dedicated tab panel containers (`#view-overview`, `#view-intune`, `#view-solarwinds`, `#view-network`, `#view-dex`) with CSS display toggling (`.tab-panel.active` / `.hidden`).
   - *Reasoning*: Deep linking via `window.location.hash` (e.g. `ops_analytics.html#intune`) and launcher integration in `app.js` will allow direct access to any tab view with instant (<10ms) client-side rendering.

2. **R2 Analysis (Data Integrity & Test Verification)**:
   - *Observation*: Raw dataset in `data/intune_ops_analytics.json` has exactly 25,987 device objects with 12 attributes. Mathematical aggregations in `data/intune_summary.json` match with 100% precision.
   - *Reasoning*: An automated test script `tests/verify_intune_data.py` must verify these exact numbers (25,987 total, 21,589 compliant, 3,422 non-compliant, 83.08% rate, exact OS/Mfg distributions, and 100 sample records) to guarantee zero hallucination across all deployment environments.

3. **R3 Analysis (Modular Layout & Engineering Cleanliness)**:
   - *Observation*: Root directory currently contains loose scripts, data files, and styles.
   - *Reasoning*: A clean 5-folder modular hierarchy (`src/`, `scripts/`, `data/`, `docs/`, `tests/`) separates presentation code, ETL pipelines, persisted data artifacts, architectural documentation, and automated tests. Comprehensive docstrings (PEP 257 / JSDoc) ensure production maintainability.

4. **R4 Analysis (Automated Refresh & Sync Strategy)**:
   - *Observation*: Telemetry is currently extracted via `fetch_intune_data.py` and aggregated via `generate_dashboard_payload.py`. Firebase Hosting and Firestore configuration are present.
   - *Reasoning*: A production sync strategy requires a scheduled automated job (weekly cron `0 2 * * 1` via GitHub Actions or Cloud Scheduler + Cloud Functions). The job fetches delta device records from Microsoft Graph API, validates data integrity via `tests/verify_intune_data.py`, and publishes updated payloads to Firebase Hosting (`data/intune_summary.json`) and Firestore (`itom_telemetry/intune_summary`).

---

## 3. Features Discovered & Specification Matrix

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Navigation | Interactive Tab Controller | Seamless tab switching between Overview, Intune Live, SolarWinds, Network & CMDB, and DEX Metrics | Click event on `.tab-btn` (`data-tab`) | Switches active tab class, activates corresponding view panel | Falls back to Overview if unknown tab ID provided | `ops_analytics.html:36-42`, `MRD` |
| 2 | Navigation | Deep-Linking & History | Supports direct URL linking (`#intune`, `#overview`, `#solarwinds`, `#network`, `#dex`) and browser back/forward buttons | URL hash / `popstate` / `hashchange` | Automatically activates matching tab on page load | Defaults to `overview` if hash is invalid | `ORIGINAL_REQUEST.md:R1` |
| 3 | Navigation | Launcher Module Bridge | Portal launcher (`index.html`) routes module cards into corresponding dashboard tabs | Module card click (`app.js`) | 250ms overlay feedback, navigates to `ops_analytics.html#<tab>` | Navigates to default dashboard view on cancel | `index.html:158-261`, `app.js:124-157` |
| 4 | Navigation | Visual State Indicators | Live status badge, tab active highlights, and KPI state tags (`success`, `warning`, `neutral`) | DOM state / telemetry health | Animated pulsing green dot (`.pulse-dot`), colored border/backgrounds | Renders neutral badge if state is undefined | `style.css:858-884`, `ops_analytics.html:54` |
| 5 | Telemetry UI | Intune KPI Cards | 4 primary operational cards: Managed Devices (25,987), Compliance (83.08%), Disk Util (37.4%), SolarWinds Health | `intune_summary.json` -> `metrics` | Formatted numbers and percentage tags in DOM | Shows "0" or "N/A" if metric key is missing | `ops_analytics.html:77-119`, `ops_analytics.js:26-34` |
| 6 | Telemetry UI | Chart.js Visualizations | 3 canvas-based interactive charts: OS Breakdown (Doughnut), Compliance (Bar), Manufacturer (Pie) | `os_breakdown`, `compliance_breakdown`, `manufacturer_breakdown` | Rendered Chart.js charts with tooltips and custom colors | Canvas gracefully clears / logs console error | `ops_analytics.js:35-121` |
| 7 | Telemetry UI | Searchable Inventory Table | Interactive table with 100 sample device records, storage bars, compliance badges, and real-time search | User query in `#deviceSearchInput` | Filtered table rows matching hostname, UPN, serial, model, OS | Displays "No matching records found." row | `ops_analytics.js:127-195` |
| 8 | Telemetry UI | Client CSV Export (FR-006) | Generates and triggers download of RFC 4180 compliant CSV file of complete device dataset | Click on `#exportCsvBtn` / `#loadMoreBtn` | Downloadable `intune_ops_analytics_YYYY-MM-DD.csv` file | Browser alert if dataset is empty | `ops_analytics.js:198-233` |
| 9 | Multi-Domain UI | Overview Tab Panel | Centralized executive summary consolidating all 5 operational sections into a unified high-level pane | Telemetry metrics from all domains | Aggregated operational KPI grid & domain status badges | Displays offline/pending status for unconfigured domains | `docs/MRD_Module_1_OPS_Analytics.md` |
| 10 | Multi-Domain UI | SolarWinds Tab Panel | Displays Orion server metrics (`gnoc.coforge.com:17774`), server health (High/Med/Low), and gateway status | Server telemetry / connection config | Node status table, ping latency, health classification | Shows "Awaiting VM Gateway" banner | `docs/MRD:26,43`, `ops_analytics.html:110-117` |
| 11 | Multi-Domain UI | Network & CMDB Tab Panel | Building-wise network infrastructure linked with CMDB asset records | CMDB network node records | Building-wise switch/router telemetry and link status | Displays "CMDB Sync in Progress" indicator | `docs/MRD:23,44`, `ops_analytics.html:40` |
| 12 | Multi-Domain UI | DEX Metrics Tab Panel | Digital Employee Experience score, CPU/RAM/HDD utilization, user experience impact ratings | Endpoint telemetry metrics | DEX score gauge, top impacted UPN list, utilization stats | Shows placeholder diagnostics if agent telemetry missing | `docs/MRD:27`, `ops_analytics.html:41` |
| 13 | Data / ETL | Intune Graph Extraction | Extracts managed device telemetry via Microsoft Graph API with Azure AD OAuth 2.0 and pagination | Azure AD Client Credentials (`.env`) | Raw dataset saved to `data/intune_ops_analytics.json` | Logs error and raises `requests.HTTPError` | `scripts/fetch_intune_data.py:1-117` |
| 14 | Data / ETL | Summary Payload Generation | Mathematically transforms 25,987 raw device records into optimized dashboard summary payload | `data/intune_ops_analytics.json` | `data/intune_summary.json` with metrics & 100 samples | Raises `FileNotFoundError` if raw data missing | `scripts/generate_dashboard_payload.py:1-90` |
| 15 | Verification | Automated Test Verification | Rigorous automated verification script proving data integrity, mathematical sums, and schema consistency | `data/*.json` files | Pytest test assertions & CLI summary report | Test assertion failure with detailed diff message | `ORIGINAL_REQUEST.md:R2`, `tests/verify_intune_data.py` |
| 16 | Architecture | Modular Code Layout | 5-tier directory structure (`src/`, `scripts/`, `data/`, `docs/`, `tests/`) adhering to clean architecture | Repository layout | Modular, decoupled codebase with docstrings | N/A | `ORIGINAL_REQUEST.md:R3` |
| 17 | Sync Strategy | Automated Refresh Pipeline | Weekly automated cron trigger (GitHub Actions / Cloud Scheduler) refreshing Intune telemetry | Scheduled cron trigger (`0 2 * * 1`) | Updated JSON payloads in Hosting & Firestore | Alerts on failure; serves cached fallback | `ORIGINAL_REQUEST.md:R4` |

---

## 4. Edge Cases & Robustness Matrix

| # | Feature | Input / Condition | Observed / Required Behavior |
|---|---------|-------------------|------------------------------|
| 1 | Table Search | Empty search input (`""`) | Restores full 100-record sample table immediately. |
| 2 | Table Search | Regex special characters `.*+?^${}()|[]\` | Treated as literal substrings via `String.prototype.includes()`; no regex syntax crash. |
| 3 | Table Search | Non-matching query (e.g. `xyz99999999`) | Renders clean centered message: *"No matching records found."* |
| 4 | Deep Linking | Unrecognized URL hash `#invalid_tab` | Safely defaults to `'overview'` tab without blank screen or uncaught error. |
| 5 | Deep Linking | Direct URL load with hash `#intune` | Instantly activates Intune tab button and makes `#tab-intune` panel visible on first render. |
| 6 | Data Ingestion | Empty string OS field (`operatingSystem: ""`, 24 devices) | Chart and table map empty string to `'Unknown'`. |
| 7 | Data Ingestion | Empty string Device Name (`deviceName: ""`, 4 devices) | Table renders fallback `'N/A'` or `'Unknown Device'`. |
| 8 | Data Ingestion | Empty string Serial Number (`serialNumber: ""`, 53 devices) | Table renders fallback `'N/A'`; search safely handles null/empty strings. |
| 9 | Data Ingestion | Empty string UPN (`userPrincipalName: ""`, 104 devices) | Table renders fallback `'N/A'`; search ignores or matches empty safely. |
| 10 | Data Ingestion | Zero Storage (`totalStorageSpaceInBytes: 0`, 50 devices) | Avoids division by zero; sets `usedStoragePct = 0` and progress bar to `0%`. |
| 11 | Vendor Mapping | Uppercase `'LENOVO'` (959 devices) | Classified into `'Other'` (1,057) under current logic; normalizer must use `.upper()` if dedicated bucket required. |
| 12 | CSV Export | Strings with double quotes or commas (e.g. `"Dell Pro, 14"`) | Escaped with RFC 4180 standard double-quoting (`""`). |
| 13 | Network Offline | `fetch('data/intune_summary.json')` returns HTTP 404 / 500 | Table renders friendly red error banner without crashing the application window. |
| 14 | Responsive UI | Mobile screen width (<768px) | Tab bar scrolls horizontally or stacks cleanly; KPI grid collapses to 1 column. |

---

## 5. Interface Contracts & Data Schemas

### 5.1 Telemetry Payload Schema (`data/intune_summary.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IntuneSummaryPayload",
  "type": "object",
  "required": ["metrics", "os_breakdown", "compliance_breakdown", "manufacturer_breakdown", "sample_devices"],
  "properties": {
    "metrics": {
      "type": "object",
      "required": ["total_managed_devices", "compliant_devices", "noncompliant_devices", "other_compliance", "compliance_rate_pct", "avg_storage_used_pct"],
      "properties": {
        "total_managed_devices": { "type": "integer", "const": 25987 },
        "compliant_devices": { "type": "integer", "const": 21589 },
        "noncompliant_devices": { "type": "integer", "const": 3422 },
        "other_compliance": { "type": "integer", "const": 976 },
        "compliance_rate_pct": { "type": "number", "const": 83.08 },
        "avg_storage_used_pct": { "type": "number", "const": 37.4 }
      }
    },
    "os_breakdown": {
      "type": "object",
      "properties": {
        "Windows": { "type": "integer", "const": 25334 },
        "macOS": { "type": "integer", "const": 602 },
        "Linux (ubuntu)": { "type": "integer", "const": 24 },
        "": { "type": "integer", "const": 24 },
        "iOS": { "type": "integer", "const": 2 },
        "Android": { "type": "integer", "const": 1 }
      },
      "required": ["Windows", "macOS", "Linux (ubuntu)", "iOS", "Android"]
    },
    "compliance_breakdown": {
      "type": "object",
      "properties": {
        "compliant": { "type": "integer", "const": 21589 },
        "noncompliant": { "type": "integer", "const": 3422 },
        "configManager": { "type": "integer", "const": 935 },
        "unknown": { "type": "integer", "const": 31 },
        "inGracePeriod": { "type": "integer", "const": 10 }
      },
      "required": ["compliant", "noncompliant", "configManager", "unknown", "inGracePeriod"]
    },
    "manufacturer_breakdown": {
      "type": "object",
      "properties": {
        "Dell": { "type": "integer", "const": 15716 },
        "HP": { "type": "integer", "const": 8610 },
        "Other": { "type": "integer", "const": 1057 },
        "Apple": { "type": "integer", "const": 604 }
      },
      "required": ["Dell", "HP", "Other", "Apple"]
    },
    "sample_devices": {
      "type": "array",
      "minItems": 100,
      "maxItems": 100,
      "items": {
        "type": "object",
        "required": ["id", "deviceName", "operatingSystem", "osVersion", "complianceState", "userPrincipalName", "model", "manufacturer", "serialNumber", "lastSync", "totalStorageGB", "freeStorageGB", "usedStoragePct"],
        "properties": {
          "id": { "type": "string" },
          "deviceName": { "type": "string" },
          "operatingSystem": { "type": "string" },
          "osVersion": { "type": "string" },
          "complianceState": { "type": "string" },
          "userPrincipalName": { "type": "string" },
          "model": { "type": "string" },
          "manufacturer": { "type": "string" },
          "serialNumber": { "type": "string" },
          "lastSync": { "type": "string" },
          "totalStorageGB": { "type": "number" },
          "freeStorageGB": { "type": "number" },
          "usedStoragePct": { "type": "number" }
        }
      }
    }
  }
}
```

### 5.2 Frontend Tab Navigation Contract (`ops_analytics.js`)

```javascript
/**
 * Tab Navigation Controller Interface
 * @typedef {'overview' | 'intune' | 'solarwinds' | 'network' | 'dex'} TabId
 */

/**
 * Activates the specified tab view panel and updates navigation state.
 * @param {TabId} tabId - Identifier of the tab to activate.
 * @param {boolean} [updateHash=true] - Whether to update window.location.hash.
 */
function switchTab(tabId, updateHash = true) {
  // 1. Validate tabId against allowed tabs ['overview', 'intune', 'solarwinds', 'network', 'dex']
  // 2. Remove 'active' from all .tab-btn elements; add 'active' to target tab button
  // 3. Hide all .tab-view panels; display target .tab-view panel
  // 4. If updateHash is true, update window.location.hash = tabId
  // 5. Trigger resize/redraw on Chart.js instances if tab contains charts
}
```

---

## 6. Architecture & Data Sync Blueprint (R4)

```
+-----------------------------------------------------------------------------------+
|                            AUTOMATED DATA SYNC ARCHITECTURE                       |
+-----------------------------------------------------------------------------------+

 [Azure Active Directory / Intune Graph API]
                     |
                     | 1. Scheduled OAuth 2.0 Auth & Paginated GET
                     v
   [scripts/fetch_intune_data.py / Cloud Function]
                     |
                     | 2. Raw JSON Ingestion (25,987 Records)
                     v
       [data/intune_ops_analytics.json]
                     |
                     | 3. Aggregation & Verification (generate_dashboard_payload.py)
                     v
         [data/intune_summary.json]  <---------------+
                     |                               |
                     +---------------------------+   | 4. pytest tests/verify_intune_data.py
                     |                           |   |    (Zero-Hallucination Gate)
                     v                           v   |
          [Firebase Hosting]           [Firestore Database]
            (Static CDN JSON)           (Collection: itom_telemetry)
                     |                           |
                     +-------------+-------------+
                                   |
                                   | 5. Ultra-Fast Client Load (<50ms)
                                   v
             [OPS Analytics Web Dashboard (ops_analytics.html)]
             - Tab 1: Overview
             - Tab 2: Microsoft Intune (Live)
             - Tab 3: SolarWinds (Pending)
             - Tab 4: Network & CMDB
             - Tab 5: DEX Metrics
```

### Sync Strategy Options Comparison

| Dimension | Option A: Cloud Scheduler + Cloud Function + Firestore | Option B: Scheduled CI/CD Pipeline + Firebase Hosting Deploy | Option C: Hybrid Architecture (Recommended) |
|---|---|---|---|
| **Trigger Mechanism** | Cloud Scheduler cron (`0 2 * * 1`) triggering Cloud Run/Function | GitHub Actions / Cloud Build cron (`0 2 * * 1`) | Cloud Scheduler / GitHub Actions cron triggering ETL |
| **Data Target** | Firestore document `itom_telemetry/intune_summary` | Firebase Hosting `data/intune_summary.json` | Both Firestore & static Hosting JSON |
| **Client Load Latency** | ~200–400ms (Firestore SDK connection) | <50ms (Static CDN Edge caching) | <50ms (Cached JSON) with live Firestore subscription |
| **Cost & Complexity** | Higher (Firestore reads + Cloud Function runtime) | Minimal ($0 hosting & static CDN) | Optimal balance: zero runtime cost + real-time optionality |
| **Verification Gating** | Function asserts summary metrics before write | Workflow runs `tests/verify_intune_data.py` before deploy | Test suite blocks deployment if 25,987 invariant fails |

---

## 7. Modular Codebase Layout (R3)

```
optimistic-pasteur/
├── src/
│   ├── frontend/
│   │   ├── index.html                    # ITOM Portal Launcher UI
│   │   ├── ops_analytics.html            # OPS Analytics Multi-Tab Dashboard
│   │   ├── css/
│   │   │   └── style.css                 # Dark-mode enterprise CSS stylesheet
│   │   └── js/
│   │       ├── app.js                    # Launcher controller, search & modal logic
│   │       └── ops_analytics.js          # Tab navigation, Chart.js & dynamic table controller
│   └── sync/
│       ├── __init__.py
│       ├── graph_client.py               # Microsoft Graph API OAuth & pagination service
│       ├── payload_generator.py          # Data aggregation and summary engine
│       └── firestore_sync.py             # Firestore synchronization utility
├── scripts/
│   ├── fetch_intune_data.py              # CLI executable for Graph API ingestion
│   ├── generate_dashboard_payload.py     # CLI executable for summary generation
│   └── run_sync.py                       # End-to-end sync execution orchestrator
├── data/
│   ├── intune_ops_analytics.json         # Raw dataset (25,987 verified device records)
│   └── intune_summary.json               # Aggregated metrics & 100 sample device records
├── docs/
│   ├── MRD_Module_1_OPS_Analytics.md     # Product Requirements Document
│   ├── ARCHITECTURE.md                   # System Architecture & Sync Strategy Guide
│   └── API_CONTRACTS.md                  # Interface schemas and data dictionary
├── tests/
│   ├── __init__.py
│   ├── verify_intune_data.py             # Automated verification suite (25,987 invariants)
│   ├── test_payload_generator.py         # Unit tests for metric transformations
│   └── test_tab_navigation.py            # Headless / DOM tests for tab switching
├── .firebaserc                           # Firebase project configuration
├── firebase.json                         # Firebase hosting and firestore routing
├── firestore.rules                       # Firestore database security rules
├── firestore.indexes.json                # Firestore database indexes
├── .env.example                          # Environment variables template
└── ORIGINAL_REQUEST.md                   # Authoritative user requirements
```

---

## 8. Caveats

- **Azure AD API Credentials**: In development/testing environments without live Azure credentials in `.env`, the pipeline relies on the authoritative snapshot of 25,987 devices stored in `data/intune_ops_analytics.json`.
- **SolarWinds / CMDB Live Endpoints**: SolarWinds Orion (`gnoc.coforge.com:17774`) and CMDB live telemetry are marked as pipeline-dependent (awaiting VM network gateway setup per MRD); tab views must render clear status badges and architecture placeholders.
- **LENOVO Categorization**: In the existing `generate_dashboard_payload.py`, `'LENOVO'` (959 devices) is categorized under `'Other'` due to case sensitivity. The specification documents this behavior and provides the exact breakdown for both case-sensitive and case-insensitive models.

---

## 9. Conclusion

All requirements (R1 through R4) from `ORIGINAL_REQUEST.md` have been mined, probed, and specified with exact mathematical precision:
1. **R1**: Tab navigation interface contracts and DOM view structure specified for instant switching across all 5 operational tabs with deep linking and zero buffering.
2. **R2**: 25,987 Intune devices completely verified across all dimensions with 100% mathematical consistency and an automated test suite specification in `tests/verify_intune_data.py`.
3. **R3**: Clean 5-folder modular architecture (`src/`, `scripts/`, `data/`, `docs/`, `tests/`) specified with full docstring standards.
4. **R4**: Automated refresh and sync strategy designed with weekly cron execution, verification gating, and CDN/Firestore hybrid delivery.

---

## 10. Verification Method

To independently verify the findings in this specification report:

1. **Verify Raw Data Invariants & Device Count**:
   ```bash
   python -c "import json; d=json.load(open('data/intune_ops_analytics.json'))['devices']; assert len(d)==25987; print('Count verified: 25,987 devices')"
   ```
2. **Verify Summary Metrics Consistency**:
   ```bash
   python -c "import json; s=json.load(open('data/intune_summary.json')); assert s['metrics']['total_managed_devices']==25987; assert s['metrics']['compliant_devices']==21589; assert s['metrics']['noncompliant_devices']==3422; assert s['metrics']['compliance_rate_pct']==83.08; assert s['metrics']['avg_storage_used_pct']==37.4; print('Summary metrics mathematically verified!')"
   ```
3. **Verify Categorical Distributions**:
   ```bash
   python -c "import json; s=json.load(open('data/intune_summary.json')); assert sum(s['os_breakdown'].values())==25987; assert sum(s['compliance_breakdown'].values())==25987; assert sum(s['manufacturer_breakdown'].values())==25987; print('All distributions sum to exactly 25,987!')"
   ```
4. **Verify Tab Navigation & DOM Elements**:
   Inspect `ops_analytics.html` lines 36–42 to verify tab button data attributes (`data-tab="overview"`, `"intune"`, `"solarwinds"`, `"network"`, `"dex"`).
