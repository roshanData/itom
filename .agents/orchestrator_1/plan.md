# Orchestrator Execution Plan: ITOM OPS Analytics & Microsoft Intune Integration

## 1. Survey Phase
- Spawn 3 parallel Explorers / Spec Miners:
  - Explorer 1: Codebase structure, `ops_analytics.html`, dashboard tab switching mechanism, and existing navigation scripts/assets.
  - Explorer 2: Intune telemetry datasets (25,987 devices), raw data files, data schema, OS breakdown, compliance, manufacturer distribution, and summary calculations.
  - Spec Miner: Requirements analysis, automated refresh & sync strategy options (Cloud Functions/cron/Firestore/Hosting), modular architecture layout (`src/`, `scripts/`, `data/`, `docs/`, `tests/`), and test verification requirements.

## 2. Synthesis & Global Decomposition (PROJECT.md)
- Synthesize explorer findings into `PROJECT.md` (Architecture, Feature Inventory, Milestone Plan, Interface Contracts, Code Layout).
- Establish Dual Track: Implementation Track and E2E Testing Track.

## 3. Dual Track Execution
- **E2E Testing Track**:
  - Spawn E2E Testing Orchestrator / Test Writer to implement test runner, `tests/verify_intune_data.py`, unit & E2E tests (Tiers 1-4).
  - Publish `TEST_INFRA.md` and `TEST_READY.md`.
- **Implementation Track**:
  - Milestone M1: Codebase Restructuring & Modular Architecture (`src/`, `scripts/`, `data/`, `docs/`, `tests/`).
  - Milestone M2: Data Extraction & Pipeline Verification (25,987 devices numeric consistency, OS, compliance, manufacturer metrics).
  - Milestone M3: Interactive Tab Navigation & Live Telemetry UI (`ops_analytics.html` tabs: "Microsoft Intune (Live)", "Overview", "SolarWinds", "Network", "DEX").
  - Milestone M4: Automated Refresh & Data Sync Strategy (Cloud Function/cron trigger, sync scripts, documentation).
  - Milestone M5 (Final Integration): Pass 100% E2E test suite + Phase 2 Adversarial Coverage Hardening (Tier 5).

## 4. Verification & Audit Gating
- Reviewers, Challengers, and Forensic Auditors on all milestones.
- Strict binary veto on audit integrity violations.

## 5. Final Handoff & Reporting
- Final validation report and human reporting summary.
