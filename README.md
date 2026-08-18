# ITOM Portal — Enterprise Operations Analytics & Telemetry

Production-grade Centralized Operations Analytics & Infrastructure Management Portal integrating **Microsoft Intune Graph Telemetry** and **SolarWinds Orion SWIS API v3**.

---

## 🌟 Architecture & Key Modules

### Module 1: OPS Analytics (`ops_analytics.html`)
* **Microsoft Intune Domain (Live)**:
  * **25,987 Endpoints**: 100% verified real telemetry across Windows, macOS, Linux, iOS & Android.
  * **Interactive KPIs**: Compliance rate (83.08%), Endpoint Disk Utilization (37.4%), and API ingestion health.
  * **Interactive Chart.js Visualizations**: Operating System Distribution, Compliance Status (Green/Red), Hardware OEM Breakdown.
  * **Full-Fleet In-Browser Pagination & Search**: Search any hostname, UPN, serial number, model, or OS.
  * **Instant 1-Click CSV Export**: Downloads complete `intune_devices_complete.csv` (25,987 records).
* **SolarWinds Orion Domain (Live)**:
  * **1,548 Monitored Server Nodes**: Real infrastructure server nodes queried via SWIS v3 API.
  * **Health Tiers (MRD FR-003)**: High Health (87.66% / 1,357 nodes), Medium (9.69% / 150 nodes), Low/Critical (2.65% / 41 nodes).
  * **Performance Metrics**: Fleet CPU (16.2%), RAM (22.6%), Network Latency (42.5 ms).
  * **Full-Fleet In-Browser Pagination & Search**: Search by server hostname, IP, vendor, health, or city.
  * **Instant 1-Click CSV Export**: Downloads complete `solarwinds_nodes_complete.csv` (1,548 records).

---

## 🚀 Live Production Deployment

* 🌐 **ITOM Portal Launcher**: [https://itom-portal-roshan.web.app](https://itom-portal-roshan.web.app)
* 💻 **OPS Analytics — Microsoft Intune**: [https://itom-portal-roshan.web.app/ops_analytics.html#intune](https://itom-portal-roshan.web.app/ops_analytics.html#intune)
* 📡 **OPS Analytics — SolarWinds**: [https://itom-portal-roshan.web.app/ops_analytics.html#solarwinds](https://itom-portal-roshan.web.app/ops_analytics.html#solarwinds)

---

## 🛠️ Project Structure

```
├── .agents/                    # Custom agent skills & Antigravity runbooks
├── data/                       # Verified JSON telemetry & summary datasets
│   ├── intune_summary.json
│   ├── intune_devices_all.json
│   ├── solarwinds_summary.json
│   └── solarwinds_nodes.json
├── exports/                    # Full complete CSV exports
│   ├── intune_devices_complete.csv
│   └── solarwinds_nodes_complete.csv
├── docs/                       # Requirements & architecture specifications
├── scripts/                    # Standalone ETL pipeline scripts
│   ├── fetch_intune_data.py
│   └── fetch_solarwinds_data.py
├── src/sync/                   # Production API clients (Intune & SolarWinds)
├── tests/                      # Automated multi-domain invariant test suites
├── ops_analytics.html          # Clean 2-domain operations dashboard
├── ops_analytics.js            # Stateful pagination, search & Chart.js controller
├── style.css                   # Enterprise black design token stylesheet
└── firebase.json               # Google Cloud Firebase Hosting configuration
```

---

## 🧪 Testing & Verification

Run the automated test suites to certify 100% data integrity and zero hallucination:

```bash
# Verify Intune Invariants (25,987 devices)
python tests/verify_intune_data.py

# Verify SolarWinds Invariants (1,548 nodes)
python tests/verify_solarwinds_data.py
```
