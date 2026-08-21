# ITOM OPS Analytics & Microsoft Intune Integration — API Contracts & Data Dictionary

## 1. Overview
This document defines the formal data contracts, API schemas, payload specifications, and type interfaces across the ITOM Operations Analytics ecosystem.

---

## 2. Microsoft Graph Intune Telemetry Ingestion Contract

### 2.1 Azure AD Token Endpoint
- **URL**: `POST https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token`
- **Content-Type**: `application/x-www-form-urlencoded`
- **Request Parameters**:
  | Field | Type | Description |
  |---|---|---|
  | `client_id` | string (UUID) | Registered Azure AD App Client ID |
  | `client_secret` | string | Secret generated in Azure App Registration |
  | `scope` | string | `https://graph.microsoft.com/.default` |
  | `grant_type` | string | `client_credentials` |

- **Response Body (`200 OK`)**:
  ```json
  {
    "token_type": "Bearer",
    "expires_in": 3599,
    "ext_expires_in": 3599,
    "access_token": "eyJ0eXAiOiJKV1QiLC..."
  }
  ```

### 2.2 Managed Devices Endpoint
- **URL**: `GET https://graph.microsoft.com/v1.0/deviceManagement/managedDevices`
- **Headers**:
  - `Authorization`: `Bearer {access_token}`
  - `Accept`: `application/json`
  - `ConsistencyLevel`: `eventual`
- **OData Query Parameters**:
  - `$select`: `id,deviceName,operatingSystem,osVersion,complianceState,userPrincipalName,model,manufacturer,serialNumber,lastSyncDateTime,totalStorageSpaceInBytes,freeStorageSpaceInBytes`
  - `$top`: `100` (configurable 10..999)

- **Response Schema (`200 OK`)**:
  ```json
  {
    "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#deviceManagement/managedDevices",
    "@odata.nextLink": "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices?$select=...&$skiptoken=X'...",
    "value": [
      {
        "id": "4d0a62f4-a48d-48e9-b844-0a0a7ce03e14",
        "deviceName": "LAP-NJ-81003082",
        "operatingSystem": "Windows",
        "osVersion": "10.0.26200.8457",
        "complianceState": "noncompliant",
        "userPrincipalName": "Janhvi.Tendulkar@example.com",
        "model": "Dell Pro 14 PC14250",
        "manufacturer": "Dell Inc.",
        "serialNumber": "J02XDJ4",
        "lastSyncDateTime": "2026-06-02T14:34:54Z",
        "totalStorageSpaceInBytes": 508759539712,
        "freeStorageSpaceInBytes": 359286460416
      }
    ]
  }
  ```

---

## 3. Raw Data Store Contract (`data/intune_ops_analytics.json`)

```typescript
interface IntuneRawPayload {
  summary: {
    total_devices: number;
    os_breakdown: Record<string, number>;
    compliance_breakdown: Record<string, number>;
  };
  devices: Array<{
    id: string;
    deviceName: string;
    operatingSystem: string;
    osVersion: string;
    complianceState: "compliant" | "noncompliant" | "configManager" | "unknown" | "inGracePeriod" | string;
    userPrincipalName: string;
    model: string;
    manufacturer: string;
    serialNumber: string;
    lastSyncDateTime: string;
    totalStorageSpaceInBytes: number;
    freeStorageSpaceInBytes: number;
  }>;
}
```

---

## 4. Aggregated Dashboard Summary Contract (`data/intune_summary.json`)

```typescript
interface IntuneSummaryPayload {
  metrics: {
    /** Total managed endpoints extracted (authoritative: 25,987) */
    total_managed_devices: number;
    /** Compliant devices (authoritative: 21,589) */
    compliant_devices: number;
    /** Non-compliant devices (authoritative: 3,422) */
    noncompliant_devices: number;
    /** Other compliance states (authoritative: 976) */
    other_compliance: number;
    /** Percentage of compliant devices: round((21589 / 25987) * 100, 2) = 83.08 */
    compliance_rate_pct: number;
    /** Fleet average storage utilization: round((totalUsed / totalCapacity) * 100, 1) = 37.4 */
    avg_storage_used_pct: number;
  };

  /** Distribution across operating systems */
  os_breakdown: {
    Windows: number;           // 25,334
    macOS: number;             // 602
    "Linux (ubuntu)": number;  // 24
    "": number;                // 24 (Unspecified)
    iOS: number;               // 2
    Android: number;           // 1
  };

  /** Distribution across compliance policy states */
  compliance_breakdown: {
    compliant: number;         // 21,589
    noncompliant: number;      // 3,422
    configManager: number;     // 935
    unknown: number;           // 31
    inGracePeriod: number;     // 10
  };

  /** Normalized manufacturer distribution */
  manufacturer_breakdown: {
    Dell: number;              // 15,716
    HP: number;                // 8,610
    Lenovo: number;            // 959 (normalized from "LENOVO")
    Apple: number;             // 604
    Other: number;             // 98
  };

  /** Sample device records formatted for client-side table rendering */
  sample_devices: Array<{
    id: string;
    deviceName: string;
    operatingSystem: string;
    osVersion: string;
    complianceState: string;
    userPrincipalName: string;
    model: string;
    manufacturer: string;
    serialNumber: string;
    lastSync: string;
    totalStorageGB: number;
    freeStorageGB: number;
    usedStoragePct: number;
  }>;
}
```

---

## 5. Frontend Interfaces & Navigation Controller

### 5.1 Tab Controller Interface (`ops_analytics.js`)
```typescript
type TabId = "overview" | "intune" | "solarwinds" | "network" | "dex";

interface TabNavigationController {
  /**
   * Activates specified tab, adjusts DOM view visibility, and updates location.hash.
   */
  switchTab(tabId: TabId, updateHash?: boolean): void;

  /**
   * Returns current active tab identifier.
   */
  getActiveTab(): TabId;

  /**
   * Initializes URL hash listener and default tab routing.
   */
  initTabRouter(): void;
}
```

### 5.2 Device Search & Filter Interface
```typescript
interface DeviceSearchFilter {
  /**
   * Filters in-memory device list by search query matching hostname, UPN, serial, model, or OS.
   */
  filterDevices(query: string, devices: Array<SampleDevice>): Array<SampleDevice>;

  /**
   * Renders filtered rows into table body with highlighted matches and zero-result state.
   */
  renderTable(filteredDevices: Array<SampleDevice>): void;
}
```

### 5.3 RFC 4180 CSV Export Schema
The export function generates an RFC 4180 compliant CSV file downloaded with filename `itom_intune_managed_devices_{YYYYMMDD}.csv`:

| Column Index | Header | Sample Value | Description |
|---|---|---|---|
| 0 | `Device ID` | `4d0a62f4-a48d-48e9-b844-0a0a7ce03e14` | Intune Managed Device GUID |
| 1 | `Device Name` | `LAP-NJ-81003082` | Hostname / NetBIOS name |
| 2 | `Operating System` | `Windows` | OS Family |
| 3 | `OS Version` | `10.0.26200.8457` | OS Kernel / Build Number |
| 4 | `Compliance State` | `noncompliant` | Policy Compliance Status |
| 5 | `User Principal Name` | `Janhvi.Tendulkar@example.com` | Primary user Azure UPN |
| 6 | `Model` | `Dell Pro 14 PC14250` | Hardware Model |
| 7 | `Manufacturer` | `Dell Inc.` | OEM Manufacturer |
| 8 | `Serial Number` | `J02XDJ4` | Hardware Serial / Service Tag |
| 9 | `Last Sync (UTC)` | `2026-06-02T14:34:54Z` | Timestamp of last Intune sync |
| 10 | `Total Storage (GB)` | `473.8` | Total drive capacity in GiB |
| 11 | `Free Storage (GB)` | `334.6` | Free drive capacity in GiB |
| 12 | `Used Storage (%)` | `29.4` | Utilization percentage |

---

## 6. Google Cloud Firestore Document Contract

### 6.1 Collection: `itom_telemetry` / Document: `intune_summary`
- **Document Path**: `/itom_telemetry/intune_summary`
- **Schema**: Matches `IntuneSummaryPayload` with added `_syncMetadata`:
  ```json
  {
    "metrics": { ... },
    "os_breakdown": { ... },
    "compliance_breakdown": { ... },
    "manufacturer_breakdown": { ... },
    "sample_devices": [ ... ],
    "_syncMetadata": {
      "synced_at": "2026-08-18T00:35:50Z",
      "doc_id": "intune_summary",
      "collection": "itom_telemetry",
      "status": "success",
      "offline_mode": false
    }
  }
  ```

### 6.2 Collection: `intune_devices`
- **Document Path**: `/intune_devices/{id}`
- **Document Fields**: Direct mapping of raw Intune device record properties.

---

## 7. Error Handling Contracts

| Error Type | Source Module | HTTP / Exit Code | Description |
|---|---|---|---|
| `GraphAuthError` | `src/sync/graph_client.py` | Exit 2 / HTTP 401 | Invalid Azure tenant credentials or missing API permissions |
| `GraphApiError` | `src/sync/graph_client.py` | Exit 3 / HTTP 5xx | Intune Graph endpoint throttled or unavailable |
| `AssertionError` | `src/sync/payload_generator.py` | Non-zero | Mathematical invariant discrepancy in aggregation pipeline |
| `DOMException` | `ops_analytics.js` | UI Banner | JSON summary payload missing or network fetch failure |
