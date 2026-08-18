# ITOM Portal Development & Telemetry Guidelines

## Zero-Hallucination Policy
- Never create, display, or commit mock/simulated numbers for executive metrics.
- All figures displayed on OPS Analytics must originate from verified API extractions (Microsoft Graph Intune API or SolarWinds SWIS API).
- All non-integrated sections (Network CMDB, DEX) must strictly display clean "Coming Soon / Phase 2" pipeline cards.

## Multi-Domain Telemetry Standards
- **Microsoft Intune**: 25,987 total endpoints across Windows, macOS, Linux, iOS, Android. Compliance and storage invariants must reconcile with raw Graph datasets.
- **SolarWinds Orion**: 1,548 total server nodes. Health tiers: High (Up & CPU<75% & RAM<80%), Medium (Warning or CPU/RAM 75-90%), Low/Critical (Down/Critical or CPU/RAM>90%).

## UI & Visual Design Tokens
- Background: Black (`#0B0B0B`)
- Cards & Surfaces: `#141414` with `#222222` subtle borders
- Accent Colors: `#F97316` (Orange highlights), `#10B981` (Green/High Health), `#F59E0B` (Warning), `#EF4444` (Critical)
- Dynamic Headers: Tab-aware header telemetry switching between Intune (25,987) and SolarWinds (1,548).

## Security & Secrets
- Never commit credentials to git. All client IDs, tenant secrets, and passwords must be stored exclusively in `.env` and read at runtime via environment variables.
- All user, hostname, and serial number inputs rendered in DOM tables must be sanitized through `escapeHtml()` to prevent XSS.
