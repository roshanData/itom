#!/usr/bin/env python3
"""Real-World Enterprise E2E Scenario Integration Tests (Tier 4 & Tier 3).

Executes end-to-end integration workflows simulating realistic user journeys:
1. Scenario 1: Executive ITOM Overview Drill-Down (F1, F2, F5, F9, F10, F11, F12)
2. Scenario 2: Intune Fleet Compliance Audit & BitLocker Triage (F1, F5, F6, F7, F8, F13, F14)
3. Scenario 3: Portal Launcher Deep-Link Direct Navigation (F2, F3, F4, F9, F12)
4. Scenario 4: Enterprise Hardware Refresh Audit (Lenovo/Dell/HP) (F5, F6, F7, F8, F15)
5. Scenario 5: Automated Weekly Telemetry Sync Pipeline (F13, F14, F15, F18, F19)
"""

import csv
import io
import json
import os
import sys
import unittest
from typing import Any, Dict, List

# Workspace setup
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tests.verify_intune_data import (
    classify_manufacturer,
    compute_raw_metrics,
    verify_raw_dataset
)
from tests.test_payload_generator import (
    generate_payload_from_devices,
    normalize_manufacturer
)
from tests.test_tab_navigation import (
    TabRouterSimulation,
    filter_device_records,
    generate_rfc4180_csv
)


class TestScenario1ExecutiveOverviewDrillDown(unittest.TestCase):
    """Scenario 1: Executive loads ITOM Overview, validates multi-domain health, drills down into Intune."""

    @classmethod
    def setUpClass(cls):
        raw_path = os.path.join(WORKSPACE_ROOT, "data", "intune_ops_analytics.json")
        with open(raw_path, "r", encoding="utf-8") as f:
            cls.raw_data = json.load(f)
        cls.devices = cls.raw_data["devices"]
        cls.metrics = compute_raw_metrics(cls.devices)

    def test_executive_landing_on_overview(self):
        """Step 1: Executive lands on '#overview' and reads top-level KPIs."""
        router = TabRouterSimulation("#overview")
        self.assertEqual(router.get_active_tab(), "overview")
        
        # Verify Consolidated KPIs dynamically
        tot = len(self.devices)
        self.assertEqual(self.metrics["total_devices"], tot)
        self.assertTrue(0 <= self.metrics["compliance_rate_pct"] <= 100)
        self.assertTrue(0 <= self.metrics["avg_storage_used_pct"] <= 100)

    def test_executive_drilldown_into_intune_live(self):
        """Step 2: Executive clicks 'Microsoft Intune (Live)' tab button."""
        router = TabRouterSimulation("#overview")
        active = router.switch_tab("intune")
        self.assertEqual(active, "intune")
        self.assertEqual(router.get_active_tab(), "intune")
        self.assertTrue(router.tab_states["intune"])
        self.assertFalse(router.tab_states["overview"])

    def test_executive_intune_view_integrity(self):
        """Step 3: Verify Intune view telemetry matches live fleet metrics."""
        tot = len(self.devices)
        comp = self.metrics["compliance_breakdown"]
        self.assertEqual(sum(comp.values()), tot)
        self.assertEqual(self.metrics["compliant_count"], comp.get("compliant", 0))
        self.assertEqual(self.metrics["noncompliant_count"], comp.get("noncompliant", 0))


class TestScenario2ComplianceAuditAndTriage(unittest.TestCase):
    """Scenario 2: Compliance auditor audits non-compliant devices and exports triage report."""

    @classmethod
    def setUpClass(cls):
        raw_path = os.path.join(WORKSPACE_ROOT, "data", "intune_ops_analytics.json")
        with open(raw_path, "r", encoding="utf-8") as f:
            cls.raw_data = json.load(f)
        cls.devices = cls.raw_data["devices"]
        cls.metrics = compute_raw_metrics(cls.devices)

    def test_compliance_auditor_inspects_breakdown(self):
        """Step 1: Verify non-compliant count equals raw non-compliant breakdown."""
        comp = self.metrics["compliance_breakdown"]
        noncomp = comp.get("noncompliant", 0)
        tot = self.metrics["total_devices"]
        noncomp_pct = round((noncomp / tot) * 100, 2)
        self.assertEqual(noncomp, self.metrics["noncompliant_count"])
        self.assertTrue(0 <= noncomp_pct <= 100)

    def test_compliance_search_and_triage(self):
        """Step 2: Auditor searches for non-compliant devices in interactive table."""
        sample_devices = [
            {
                "id": d["id"],
                "deviceName": d.get("deviceName", "N/A"),
                "complianceState": d.get("complianceState", "unknown"),
                "userPrincipalName": d.get("userPrincipalName", "N/A"),
                "serialNumber": d.get("serialNumber", "N/A"),
                "model": d.get("model", "N/A"),
                "operatingSystem": d.get("operatingSystem", "Unknown"),
                "osVersion": d.get("osVersion", "N/A"),
                "manufacturer": d.get("manufacturer", "N/A"),
                "totalStorageGB": 500.0, "freeStorageGB": 300.0, "usedStoragePct": 40.0,
                "lastSync": d.get("lastSyncDateTime", "N/A")
            }
            for d in self.devices[:100]
        ]
        
        # Filter for non-compliant devices in sample
        noncompliant_samples = [d for d in sample_devices if d["complianceState"].lower() == "noncompliant"]
        if noncompliant_samples:
            target_hostname = noncompliant_samples[0]["deviceName"]
            filtered = filter_device_records(sample_devices, target_hostname)
            self.assertTrue(len(filtered) >= 1)
            self.assertEqual(filtered[0]["deviceName"], target_hostname)

    def test_compliance_export_rfc4180_csv(self):
        """Step 3: Auditor exports triage report in RFC 4180 CSV format."""
        noncompliant_devices = [
            d for d in self.devices if (d.get("complianceState") or "").lower() == "noncompliant"
        ]
        self.assertEqual(len(noncompliant_devices), self.metrics["noncompliant_count"])
        
        # Export sample of 50 non-compliant devices
        csv_out = generate_rfc4180_csv(noncompliant_devices[:50])
        reader = list(csv.reader(io.StringIO(csv_out)))
        self.assertEqual(len(reader), min(51, len(noncompliant_devices) + 1))
        self.assertEqual(reader[0][0], "Device Name")
        self.assertEqual(reader[0][8], "Compliance State")


class TestScenario3LauncherDeepLinkFlow(unittest.TestCase):
    """Scenario 3: Portal Launcher deep link navigation to DEX, SolarWinds, and Network tabs."""

    def test_launcher_deep_link_solarwinds(self):
        """Step 1: Direct link to '#solarwinds' activates SolarWinds tab."""
        router = TabRouterSimulation("#solarwinds")
        self.assertEqual(router.get_active_tab(), "solarwinds")
        self.assertTrue(router.tab_states["solarwinds"])
        self.assertFalse(router.tab_states["overview"])

    def test_launcher_deep_link_dex(self):
        """Step 2: Direct link to '#dex' activates DEX Metrics tab."""
        router = TabRouterSimulation("#dex")
        self.assertEqual(router.get_active_tab(), "dex")
        self.assertTrue(router.tab_states["dex"])
        self.assertFalse(router.tab_states["solarwinds"])

    def test_launcher_deep_link_network(self):
        """Step 3: Direct link to '#network' activates Network & CMDB tab."""
        router = TabRouterSimulation("#network")
        self.assertEqual(router.get_active_tab(), "network")
        self.assertTrue(router.tab_states["network"])


class TestScenario4HardwareRefreshAudit(unittest.TestCase):
    """Scenario 4: IT Asset Manager audits OEM distribution and verifies Lenovo case fix."""

    @classmethod
    def setUpClass(cls):
        raw_path = os.path.join(WORKSPACE_ROOT, "data", "intune_ops_analytics.json")
        with open(raw_path, "r", encoding="utf-8") as f:
            cls.raw_data = json.load(f)
        cls.devices = cls.raw_data["devices"]
        cls.metrics = compute_raw_metrics(cls.devices)

    def test_hardware_oem_distribution(self):
        """Step 1: Verify OEM breakdown sum matches total devices exactly."""
        mfg = self.metrics["manufacturer_breakdown"]
        tot = len(self.devices)
        self.assertEqual(sum(mfg.values()), tot)
        for vendor in ["Dell", "HP", "Lenovo", "Apple", "Other"]:
            self.assertIn(vendor, mfg)

    def test_lenovo_normalization_guarantee(self):
        """Step 2: Verify all raw Lenovo records are normalized to 'Lenovo'."""
        lenovo_raw = [d for d in self.devices if "lenovo" in (d.get("manufacturer") or "").lower()]
        for dev in lenovo_raw:
            self.assertEqual(classify_manufacturer(dev.get("manufacturer")), "Lenovo")

    def test_hardware_refresh_filter_and_export(self):
        """Step 3: Filter Lenovo assets and verify CSV output."""
        lenovo_devices = [d for d in self.devices if "lenovo" in (d.get("manufacturer") or "").lower()]
        if lenovo_devices:
            csv_out = generate_rfc4180_csv(lenovo_devices[:20])
            reader = list(csv.reader(io.StringIO(csv_out)))
            self.assertEqual(len(reader), min(21, len(lenovo_devices) + 1))


class TestScenario5WeeklySyncPipeline(unittest.TestCase):
    """Scenario 5: Automated weekly sync ingestion, transformation, and validation."""

    @classmethod
    def setUpClass(cls):
        cls.raw_path = os.path.join(WORKSPACE_ROOT, "data", "intune_ops_analytics.json")
        with open(cls.raw_path, "r", encoding="utf-8") as f:
            cls.raw_data = json.load(f)
        cls.devices = cls.raw_data["devices"]

    def test_pipeline_step1_raw_ingestion_verification(self):
        """Pipeline Step 1: Raw ingestion invariant check."""
        metrics = verify_raw_dataset(self.raw_path)
        self.assertEqual(metrics["total_devices"], len(self.devices))
        self.assertTrue(0 <= metrics["compliance_rate_pct"] <= 100)

    def test_pipeline_step2_payload_generation(self):
        """Pipeline Step 2: Generate payload and verify contract compliance."""
        payload = generate_payload_from_devices(self.devices)
        tot = len(self.devices)
        
        # Verify Metrics
        self.assertEqual(payload["metrics"]["total_managed_devices"], tot)
        self.assertEqual(payload["metrics"]["compliant_devices"] + payload["metrics"]["noncompliant_devices"] + sum(
            v for k, v in payload["compliance_breakdown"].items() if k not in ["compliant", "noncompliant"]
        ), tot)
        self.assertTrue(0 <= payload["metrics"]["compliance_rate_pct"] <= 100)
        self.assertTrue(0 <= payload["metrics"]["avg_storage_used_pct"] <= 100)
        
        # Verify Manufacturer Breakdown
        mfg = payload["manufacturer_breakdown"]
        self.assertEqual(sum(mfg.values()), tot)


if __name__ == "__main__":
    unittest.main(verbosity=2)
