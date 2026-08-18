# Original User Request

## 2026-08-18T00:25:10+05:30

Build a production-grade, cleanly structured ITOM OPS Analytics module with verified Microsoft Intune telemetry, working interactive tab navigation, and automated sync architecture.

Working directory: c:/Users/Roshan.Sah/Documents/antigravity/optimistic-pasteur

## Requirements

### R1. Microsoft Intune & Tab Navigation Fix
Fix the tab switching on the OPS Analytics dashboard so that clicking the "Microsoft Intune (Live)", "Overview", "SolarWinds", "Network", and "DEX" tabs seamlessly filters or switches the operational views. Ensure live device data, compliance charts, and telemetry load instantly with clean UI indicators.

### R2. Independent Multi-Agent Verification & Data Integrity
Conduct an independent cross-verification of the extracted Intune data (25,987 devices) against the dashboard summaries (OS breakdown, compliance rates, manufacturer distribution). Ensure zero hallucination, strict numeric consistency, and write an automated verification test script (`tests/verify_intune_data.py`) providing documented proof of correctness.

### R3. Code Structure & Engineering Cleanliness
Organize the codebase into modular folders (`src/`, `scripts/`, `data/`, `docs/`, `tests/`), with comprehensive docstrings and comments. Ensure adherence to clean architecture principles and maintainability.

### R4. Automated Refresh & Data Sync Strategy
Design and document the automated data sync mechanism (e.g., weekly scheduled sync or automated Cloud Function/cron trigger into Firestore/Hosting) so that new telemetry is fetched and updated reliably without manual intervention.

## Acceptance Criteria

### Interactive UI & Tab Routing
- [ ] Clicking on "Microsoft Intune (Live)" and other tabs on `ops_analytics.html` dynamically updates the view and displays the relevant dataset without errors.
- [ ] Direct and launcher-based navigation works smoothly with zero infinite buffering.

### Data Accuracy & Verification
- [ ] Mathematical totals and percentages across all charts match the raw 25,987 device records exactly.
- [ ] Automated verification test script validates 100% data integrity.

### Modular Architecture
- [ ] Project files and scripts are cleanly structured with descriptive folder hierarchies and clear documentation.
