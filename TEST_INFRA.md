# E2E Test Infra: ITOM OPS Analytics & Microsoft Intune Integration

## Test Philosophy
- **Requirement-Driven & Opaque-Box**: Derived strictly from `ORIGINAL_REQUEST.md`, user specifications, and verified dataset invariants.
- **Methodology**: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.
- **Zero Hallucination Gate**: Mathematical assertions verifying that all 25,987 Intune device objects, compliance totals (21,589 compliant, 3,422 non-compliant), OS breakdowns, and manufacturer distributions reconcile with 100% precision.

## Feature Inventory & Test Mapping
| # | Feature | Requirement Source | Tier 1 (Coverage) | Tier 2 (Boundaries) | Tier 3 (Interactions) | Tier 4 (Workloads) |
|---|---------|-------------------|:-----------------:|:-------------------:|:---------------------:|:------------------:|
| 1 | Tab Navigation Controller | R1 (Tab Switching) | 5 tests | 5 tests | ✓ | ✓ |
| 2 | Deep Linking & Routing | R1 (Launcher/Direct) | 5 tests | 5 tests | ✓ | ✓ |
| 3 | Launcher Bridge Overlay | R1 (Direct Navigation)| 5 tests | 5 tests | ✓ | ✓ |
| 4 | Visual State Indicators | R1 (UI Indicators) | 5 tests | 5 tests | ✓ | ✓ |
| 5 | Live Intune KPI Cards | R1, R2 (Telemetry) | 5 tests | 5 tests | ✓ | ✓ |
| 6 | Chart.js Visualizations | R1, R2 (Charts) | 5 tests | 5 tests | ✓ | ✓ |
| 7 | Searchable Device Table | R1 (Live Search) | 5 tests | 5 tests | ✓ | ✓ |
| 8 | Complete CSV Dataset Export | R1, FR-006 (Export) | 5 tests | 5 tests | ✓ | ✓ |
| 9 | Multi-Domain Overview Panel| R1, MRD (Overview) | 5 tests | 5 tests | ✓ | ✓ |
| 10| SolarWinds Health Panel | R1, MRD (SolarWinds) | 5 tests | 5 tests | ✓ | ✓ |
| 11| Network & CMDB Panel | R1, MRD (Network) | 5 tests | 5 tests | ✓ | ✓ |
| 12| DEX Metrics Panel | R1, MRD (DEX) | 5 tests | 5 tests | ✓ | ✓ |
| 13| Intune Data Invariants (25,987)| R2 (Data Integrity) | 5 tests | 5 tests | ✓ | ✓ |
| 14| Automated Verification Script| R2 (`tests/verify_intune_data.py`)| 5 tests | 5 tests | ✓ | ✓ |
| 15| Case-Insensitive Normalization| R2 (Manufacturer Fix)| 5 tests | 5 tests | ✓ | ✓ |
| 16| Modular Codebase Layout | R3 (Folder Structure)| 5 tests | 5 tests | ✓ | ✓ |
| 17| Production Documentation | R3 (Docstrings/Specs)| 5 tests | 5 tests | ✓ | ✓ |
| 18| Automated Sync Architecture| R4 (Sync Strategy) | 5 tests | 5 tests | ✓ | ✓ |
| 19| Sync CLI Execution | R4 (Sync Pipeline) | 5 tests | 5 tests | ✓ | ✓ |

## Test Architecture
- **Master Test Runner**: `python tests/run_e2e_tests.py` (executes all test suites with structured reporting and non-zero exit code on failure).
- **Core Invariant Verification**: `python tests/verify_intune_data.py` (checks 25,987 records, sums, percentages, sample consistency).
- **Payload Engine Tests**: `python tests/test_payload_generator.py` (unit tests for aggregation and manufacturer normalization).
- **Navigation & DOM Tests**: `python tests/test_tab_navigation.py` (validates HTML tab panes, JS tab handlers, deep link parsing, search filters).
- **End-to-End Scenarios**: `python tests/test_e2e_scenarios.py` (multi-tier workload scenarios).

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Executive ITOM Overview Drill-Down | F1, F2, F5, F9, F10, F11, F12 | High |
| 2 | Intune Fleet Compliance Audit & BitLocker Triage | F1, F5, F6, F7, F8, F13, F14 | High |
| 3 | Portal Launcher Deep-Link Direct Navigation | F2, F3, F4, F9, F12 | Medium |
| 4 | Enterprise Hardware Refresh (Lenovo/Dell/HP) | F5, F6, F7, F8, F15 | High |
| 5 | Automated Weekly Telemetry Sync Pipeline | F13, F14, F15, F18, F19 | High |

## Coverage Thresholds
- **Tier 1 (Feature Coverage)**: ≥5 test cases per feature (19 × 5 = 95+ test assertions)
- **Tier 2 (Boundary & Corner Cases)**: ≥5 test cases per feature (19 × 5 = 95+ boundary checks)
- **Tier 3 (Cross-Feature Combinations)**: Pairwise coverage across major feature interactions
- **Tier 4 (Real-World Scenarios)**: ≥5 complex workflow integration scenarios
- **Total Test Assertions Target**: >200 automated checks across all tiers
