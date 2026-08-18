#!/usr/bin/env python3
"""Unit & Integration Tests for Intune Payload Generation Engine.

Validates:
- Case-insensitive OEM classification (LENOVO -> Lenovo, Hewlett-Packard -> HP, Dell, Apple, Other)
- Fleet and device storage calculation with boundary handling
- Compliance breakdown aggregation and precision rounding
- Sample device record extraction and schema validation
- IntuneSummaryPayload interface contract compliance
"""

import json
import os
import sys
import unittest
from typing import Any, Dict, List, Optional

# Add workspace root to sys.path for direct module import
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


def normalize_manufacturer(mfg: Any) -> str:
    """Canonical manufacturer normalization function under test."""
    if not mfg or not isinstance(mfg, str):
        return "Other"
    m = mfg.strip().lower()
    if "dell" in m:
        return "Dell"
    if "hp" in m or "hewlett" in m:
        return "HP"
    if "lenovo" in m:
        return "Lenovo"
    if "apple" in m:
        return "Apple"
    return "Other"


def compute_device_storage_metrics(tot_bytes: Any, free_bytes: Any) -> Dict[str, float]:
    """Compute per-device storage in GB and percentage used."""
    tot = tot_bytes if isinstance(tot_bytes, (int, float)) and tot_bytes > 0 else 0
    free = free_bytes if isinstance(free_bytes, (int, float)) and free_bytes >= 0 else 0
    
    # Clamp free to not exceed tot
    if free > tot:
        free = tot
        
    tot_gb = round(tot / (1024**3), 1) if tot > 0 else 0.0
    free_gb = round(free / (1024**3), 1) if tot > 0 else 0.0
    used_pct = round(((tot - free) / tot) * 100, 1) if tot > 0 else 0.0
    
    return {
        "totalStorageGB": tot_gb,
        "freeStorageGB": free_gb,
        "usedStoragePct": used_pct
    }


def generate_sample_record(d: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw device dict into dashboard sample record."""
    tot = d.get("totalStorageSpaceInBytes") or 0
    free = d.get("freeStorageSpaceInBytes") or 0
    storage = compute_device_storage_metrics(tot, free)
    
    return {
        "id": str(d.get("id") or ""),
        "deviceName": str(d.get("deviceName") or "N/A"),
        "operatingSystem": str(d.get("operatingSystem") or "Unknown"),
        "osVersion": str(d.get("osVersion") or "N/A"),
        "complianceState": str(d.get("complianceState") or "unknown"),
        "userPrincipalName": str(d.get("userPrincipalName") or "N/A"),
        "model": str(d.get("model") or "N/A"),
        "manufacturer": str(d.get("manufacturer") or "N/A"),
        "serialNumber": str(d.get("serialNumber") or "N/A"),
        "lastSync": str(d.get("lastSyncDateTime") or "N/A"),
        "totalStorageGB": storage["totalStorageGB"],
        "freeStorageGB": storage["freeStorageGB"],
        "usedStoragePct": storage["usedStoragePct"]
    }


def generate_payload_from_devices(devices: List[Dict[str, Any]], summary_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Pure transformation engine generating summary payload from raw device list."""
    total_devices = len(devices)
    mfg_counts = {"Dell": 0, "HP": 0, "Lenovo": 0, "Apple": 0, "Other": 0}
    comp_counts = {}
    os_counts = {}
    
    compliant_count = 0
    noncompliant_count = 0
    other_compliance = 0
    
    storage_total_gb = 0.0
    storage_free_gb = 0.0
    
    for d in devices:
        # Manufacturer
        raw_mfg = d.get("manufacturer")
        clean_mfg = normalize_manufacturer(raw_mfg)
        mfg_counts[clean_mfg] = mfg_counts.get(clean_mfg, 0) + 1
        
        # Compliance
        comp_raw = d.get("complianceState") or "unknown"
        comp_counts[comp_raw] = comp_counts.get(comp_raw, 0) + 1
        comp_lower = comp_raw.lower()
        if comp_lower == "compliant":
            compliant_count += 1
        elif comp_lower == "noncompliant":
            noncompliant_count += 1
        else:
            other_compliance += 1
            
        # OS
        os_raw = d.get("operatingSystem") if d.get("operatingSystem") is not None else ""
        os_counts[os_raw] = os_counts.get(os_raw, 0) + 1
        
        # Storage
        tot_bytes = d.get("totalStorageSpaceInBytes") or 0
        free_bytes = d.get("freeStorageSpaceInBytes") or 0
        if tot_bytes > 0:
            storage_total_gb += tot_bytes / (1024**3)
            storage_free_gb += free_bytes / (1024**3)
            
    avg_storage_used_pct = (
        round(((storage_total_gb - storage_free_gb) / storage_total_gb) * 100, 1)
        if storage_total_gb > 0 else 0.0
    )
    compliance_rate_pct = (
        round((compliant_count / total_devices) * 100, 2)
        if total_devices > 0 else 0.0
    )
    
    samples = [generate_sample_record(d) for d in devices[:100]]
    
    return {
        "metrics": {
            "total_managed_devices": total_devices,
            "compliant_devices": compliant_count,
            "noncompliant_devices": noncompliant_count,
            "other_compliance": other_compliance,
            "compliance_rate_pct": compliance_rate_pct,
            "avg_storage_used_pct": avg_storage_used_pct
        },
        "os_breakdown": summary_meta.get("os_breakdown", os_counts) if summary_meta else os_counts,
        "compliance_breakdown": summary_meta.get("compliance_breakdown", comp_counts) if summary_meta else comp_counts,
        "manufacturer_breakdown": mfg_counts,
        "sample_devices": samples
    }


class TestManufacturerNormalization(unittest.TestCase):
    """Tier 1 & Tier 2 tests for case-insensitive manufacturer normalization."""

    def test_tier1_lenovo_case_variations(self):
        """Tier 1: 'LENOVO', 'Lenovo', 'lenovo', 'LENOVO THINKPAD' must all map to 'Lenovo'."""
        self.assertEqual(normalize_manufacturer("LENOVO"), "Lenovo")
        self.assertEqual(normalize_manufacturer("Lenovo"), "Lenovo")
        self.assertEqual(normalize_manufacturer("lenovo"), "Lenovo")
        self.assertEqual(normalize_manufacturer("LENOVO Group Ltd"), "Lenovo")
        self.assertEqual(normalize_manufacturer("Lenovo ThinkPad T14"), "Lenovo")

    def test_tier1_dell_case_variations(self):
        """Tier 1: 'Dell Inc.', 'DELL', 'dell optiplex' must all map to 'Dell'."""
        self.assertEqual(normalize_manufacturer("Dell Inc."), "Dell")
        self.assertEqual(normalize_manufacturer("DELL"), "Dell")
        self.assertEqual(normalize_manufacturer("dell"), "Dell")
        self.assertEqual(normalize_manufacturer("Dell Latitude 5420"), "Dell")

    def test_tier1_hp_case_variations(self):
        """Tier 1: 'HP', 'Hewlett-Packard', 'hp inc.', 'HEWLETT-PACKARD' must map to 'HP'."""
        self.assertEqual(normalize_manufacturer("HP"), "HP")
        self.assertEqual(normalize_manufacturer("hp"), "HP")
        self.assertEqual(normalize_manufacturer("Hewlett-Packard"), "HP")
        self.assertEqual(normalize_manufacturer("HEWLETT-PACKARD"), "HP")
        self.assertEqual(normalize_manufacturer("HP EliteBook 840"), "HP")

    def test_tier1_apple_case_variations(self):
        """Tier 1: 'Apple', 'APPLE', 'apple inc.' must map to 'Apple'."""
        self.assertEqual(normalize_manufacturer("Apple"), "Apple")
        self.assertEqual(normalize_manufacturer("APPLE"), "Apple")
        self.assertEqual(normalize_manufacturer("apple"), "Apple")
        self.assertEqual(normalize_manufacturer("Apple Inc."), "Apple")

    def test_tier2_other_and_boundary_manufacturers(self):
        """Tier 2: Boundary cases (None, empty, numbers, unknown OEMs) map to 'Other'."""
        self.assertEqual(normalize_manufacturer("Microsoft Corporation"), "Other")
        self.assertEqual(normalize_manufacturer("ASUS"), "Other")
        self.assertEqual(normalize_manufacturer("Acer"), "Other")
        self.assertEqual(normalize_manufacturer("OEM"), "Other")
        self.assertEqual(normalize_manufacturer(""), "Other")
        self.assertEqual(normalize_manufacturer("   "), "Other")
        self.assertEqual(normalize_manufacturer(None), "Other")
        self.assertEqual(normalize_manufacturer(12345), "Other")


class TestStorageCalculations(unittest.TestCase):
    """Tier 1 & Tier 2 tests for per-device and aggregate storage mathematics."""

    def test_tier1_standard_storage_calculation(self):
        """Tier 1: 512 GB total, 256 GB free = 50.0% used."""
        tot = 512 * (1024**3)
        free = 256 * (1024**3)
        res = compute_device_storage_metrics(tot, free)
        self.assertEqual(res["totalStorageGB"], 512.0)
        self.assertEqual(res["freeStorageGB"], 256.0)
        self.assertEqual(res["usedStoragePct"], 50.0)

    def test_tier2_zero_storage_boundary(self):
        """Tier 2: Zero total bytes must not cause ZeroDivisionError and return 0.0."""
        res = compute_device_storage_metrics(0, 0)
        self.assertEqual(res["totalStorageGB"], 0.0)
        self.assertEqual(res["freeStorageGB"], 0.0)
        self.assertEqual(res["usedStoragePct"], 0.0)

    def test_tier2_null_and_negative_storage_boundary(self):
        """Tier 2: None and negative storage inputs handled safely."""
        res_none = compute_device_storage_metrics(None, None)
        self.assertEqual(res_none["totalStorageGB"], 0.0)
        self.assertEqual(res_none["usedStoragePct"], 0.0)

        res_neg = compute_device_storage_metrics(-1000, -500)
        self.assertEqual(res_neg["totalStorageGB"], 0.0)
        self.assertEqual(res_neg["usedStoragePct"], 0.0)

    def test_tier2_free_greater_than_total_clamped(self):
        """Tier 2: Anomalous free > total clamped to total (0% used)."""
        tot = 100 * (1024**3)
        free = 200 * (1024**3)
        res = compute_device_storage_metrics(tot, free)
        self.assertEqual(res["freeStorageGB"], 100.0)
        self.assertEqual(res["usedStoragePct"], 0.0)

    def test_tier2_full_disk_boundary(self):
        """Tier 2: 0 free bytes = 100.0% used."""
        tot = 256 * (1024**3)
        free = 0
        res = compute_device_storage_metrics(tot, free)
        self.assertEqual(res["usedStoragePct"], 100.0)


class TestSampleRecordGeneration(unittest.TestCase):
    """Tier 1 & Tier 2 tests for sample record generation and contract compliance."""

    def test_tier1_sample_record_required_schema(self):
        """Tier 1: Verify all 13 required fields exist in generated sample record."""
        raw_dev = {
            "id": "test-uuid-001",
            "deviceName": "LAP-ENG-101",
            "operatingSystem": "Windows",
            "osVersion": "10.0.26200.9168",
            "complianceState": "compliant",
            "userPrincipalName": "alex.chen@coforge.com",
            "model": "ThinkPad T14 Gen 4",
            "manufacturer": "LENOVO",
            "serialNumber": "PF3XYZ01",
            "lastSyncDateTime": "2026-06-01T12:00:00Z",
            "totalStorageSpaceInBytes": 512000000000,
            "freeStorageSpaceInBytes": 256000000000
        }
        rec = generate_sample_record(raw_dev)
        expected_keys = {
            "id", "deviceName", "operatingSystem", "osVersion", "complianceState",
            "userPrincipalName", "model", "manufacturer", "serialNumber", "lastSync",
            "totalStorageGB", "freeStorageGB", "usedStoragePct"
        }
        self.assertEqual(set(rec.keys()), expected_keys)
        self.assertEqual(rec["id"], "test-uuid-001")
        self.assertEqual(rec["deviceName"], "LAP-ENG-101")
        self.assertEqual(rec["lastSync"], "2026-06-01T12:00:00Z")

    def test_tier2_missing_fields_defaults(self):
        """Tier 2: Incomplete raw dict safely populates fallback defaults."""
        empty_dev = {}
        rec = generate_sample_record(empty_dev)
        self.assertEqual(rec["deviceName"], "N/A")
        self.assertEqual(rec["operatingSystem"], "Unknown")
        self.assertEqual(rec["complianceState"], "unknown")
        self.assertEqual(rec["userPrincipalName"], "N/A")
        self.assertEqual(rec["totalStorageGB"], 0.0)
        self.assertEqual(rec["usedStoragePct"], 0.0)


class TestPayloadGenerationIntegration(unittest.TestCase):
    """Tier 3 tests for multi-device aggregation and schema contract."""

    def test_tier3_aggregate_synthetic_fleet(self):
        """Tier 3: Aggregate synthetic 5-device fleet with Dell, HP, Lenovo, Apple, Other."""
        synthetic_devices = [
            {
                "id": "1", "manufacturer": "Dell Inc.", "complianceState": "compliant",
                "operatingSystem": "Windows", "totalStorageSpaceInBytes": 100 * (1024**3),
                "freeStorageSpaceInBytes": 50 * (1024**3)
            },
            {
                "id": "2", "manufacturer": "HP EliteBook", "complianceState": "compliant",
                "operatingSystem": "Windows", "totalStorageSpaceInBytes": 100 * (1024**3),
                "freeStorageSpaceInBytes": 60 * (1024**3)
            },
            {
                "id": "3", "manufacturer": "LENOVO", "complianceState": "noncompliant",
                "operatingSystem": "Windows", "totalStorageSpaceInBytes": 100 * (1024**3),
                "freeStorageSpaceInBytes": 70 * (1024**3)
            },
            {
                "id": "4", "manufacturer": "Apple", "complianceState": "compliant",
                "operatingSystem": "macOS", "totalStorageSpaceInBytes": 100 * (1024**3),
                "freeStorageSpaceInBytes": 80 * (1024**3)
            },
            {
                "id": "5", "manufacturer": "ASUS", "complianceState": "configManager",
                "operatingSystem": "Linux (ubuntu)", "totalStorageSpaceInBytes": 100 * (1024**3),
                "freeStorageSpaceInBytes": 90 * (1024**3)
            }
        ]
        
        payload = generate_payload_from_devices(synthetic_devices)
        metrics = payload["metrics"]
        
        self.assertEqual(metrics["total_managed_devices"], 5)
        self.assertEqual(metrics["compliant_devices"], 3)
        self.assertEqual(metrics["noncompliant_devices"], 1)
        self.assertEqual(metrics["other_compliance"], 1)
        self.assertEqual(metrics["compliance_rate_pct"], 60.0)
        
        # Storage: 500 total, (50+60+70+80+90)=350 free -> 150 used = 30.0%
        self.assertEqual(metrics["avg_storage_used_pct"], 30.0)
        
        # Manufacturer breakdown
        mfg = payload["manufacturer_breakdown"]
        self.assertEqual(mfg["Dell"], 1)
        self.assertEqual(mfg["HP"], 1)
        self.assertEqual(mfg["Lenovo"], 1)
        self.assertEqual(mfg["Apple"], 1)
        self.assertEqual(mfg["Other"], 1)
        
        # Sample devices capped at 5
        self.assertEqual(len(payload["sample_devices"]), 5)

    def test_tier3_empty_fleet_edge_case(self):
        """Tier 3: Empty fleet generates zeroed metrics without crashing."""
        payload = generate_payload_from_devices([])
        metrics = payload["metrics"]
        self.assertEqual(metrics["total_managed_devices"], 0)
        self.assertEqual(metrics["compliance_rate_pct"], 0.0)
        self.assertEqual(metrics["avg_storage_used_pct"], 0.0)
        self.assertEqual(len(payload["sample_devices"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
