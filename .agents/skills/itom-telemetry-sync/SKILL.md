---
name: itom-telemetry-sync
description: Standard operating procedure for extracting, validating, and publishing multi-domain telemetry from Microsoft Intune and SolarWinds Orion into Cloud Firestore and the ITOM Portal.
---

# ITOM Telemetry Sync & Quality Gate Runbook

## Workflow Overview
1. **Intune Telemetry Sync**:
   - Run `python scripts/fetch_intune_data.py` (reads `.env` OAuth credentials).
   - Generates `data/intune_ops_analytics.json` and `data/intune_summary.json`.
   - Run `python tests/verify_intune_data.py` to ensure 100% mathematical invariant match.

2. **SolarWinds Telemetry Sync**:
   - Run `python scripts/fetch_solarwinds_data.py` (reads `.env` SWIS credentials).
   - Generates `data/solarwinds_nodes.json` and `data/solarwinds_summary.json`.
   - Run `python tests/verify_solarwinds_data.py` to ensure health classification tiers match $1357 + 150 + 41 = 1548$.

3. **Cloud & Web Deployment**:
   - Run `npx -y firebase-tools deploy --only hosting --project itom-portal-roshan`.
   - Verify live URL: `https://itom-portal-roshan.web.app/ops_analytics.html`.
