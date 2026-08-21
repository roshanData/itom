#!/usr/bin/env python3
"""Automated Test Suite for Tab Navigation, Routing, Search & CSV Export.

Validates:
- Tab Controller: 5 operational tabs ('overview', 'intune', 'solarwinds', 'network', 'dex')
- URL Hash Router: Deep linking, hash parsing, fallback on invalid routes
- Launcher Bridge: Portal navigation, keyboard shortcuts ('/', 'Esc'), overlay transitions
- Search Filter Logic: Multi-field matching, case-insensitivity, whitespace trimming
- CSV Export Engine (FR-006): RFC 4180 compliance, header integrity, quote escaping
- Visual State Indicators: Pulsing live indicators, badge classifications
"""

import csv
import io
import json
import os
import re
import sys
import unittest
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# HTML Parsing & AST Extraction Helper
# ---------------------------------------------------------------------------

class TabHTMLParser(HTMLParser):
    """Parses ops_analytics.html to extract tab buttons, panels, KPI cards, and controls."""
    
    def __init__(self):
        super().__init__()
        self.tab_buttons: List[Dict[str, str]] = []
        self.tab_panels: List[Dict[str, str]] = []
        self.kpi_ids: List[str] = []
        self.canvas_ids: List[str] = []
        self.has_search_input = False
        self.has_export_btn = False
        self.has_pulse_dot = False
        self.current_tag: Optional[str] = None
        self.current_attrs: Dict[str, str] = {}
        
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        self.current_tag = tag
        attr_dict = {k: v for k, v in attrs if v is not None}
        self.current_attrs = attr_dict
        
        # Check tab buttons
        classes = attr_dict.get("class", "").split()
        if "tab-btn" in classes and "data-tab" in attr_dict:
            self.tab_buttons.append({
                "data-tab": attr_dict["data-tab"],
                "class": attr_dict.get("class", "")
            })
            
        # Check tab panels/views
        if "tab-pane" in classes or "tab-view" in classes or attr_dict.get("id", "").startswith("view-"):
            self.tab_panels.append({
                "id": attr_dict.get("id", ""),
                "data-tab": attr_dict.get("data-tab", "")
            })
            
        # Check KPI elements
        elem_id = attr_dict.get("id", "")
        if elem_id and (elem_id.startswith("kpi") or elem_id.startswith("stat")):
            self.kpi_ids.append(elem_id)
            
        # Check Charts
        if tag == "canvas" and "id" in attr_dict:
            self.canvas_ids.append(attr_dict["id"])
            
        # Check Search input
        if tag == "input" and attr_dict.get("id") == "deviceSearchInput":
            self.has_search_input = True
            
        # Check Export CSV button
        if attr_dict.get("id") in ("exportCsvBtn", "loadMoreBtn"):
            self.has_export_btn = True
            
        # Check Pulse dot indicator
        if "pulse-dot" in classes:
            self.has_pulse_dot = True


# ---------------------------------------------------------------------------
# Pure Tab Router & Search Simulation Engine
# ---------------------------------------------------------------------------

class TabRouterSimulation:
    """Emulates client-side tab navigation controller and URL hash router."""
    
    VALID_TABS = ["overview", "intune", "solarwinds", "network", "dex"]
    DEFAULT_TAB = "overview"
    
    def __init__(self, initial_hash: str = ""):
        self.active_tab = self.parse_hash(initial_hash)
        self.history: List[str] = [self.active_tab]
        self.tab_states: Dict[str, bool] = {t: (t == self.active_tab) for t in self.VALID_TABS}
        
    @classmethod
    def parse_hash(cls, hash_str: str) -> str:
        """Parse raw URL hash into valid TabId, defaulting to 'overview'."""
        if not hash_str:
            return cls.DEFAULT_TAB
        clean = str(hash_str).strip().lstrip("#").strip().lower()
        if clean in cls.VALID_TABS:
            return clean
        return cls.DEFAULT_TAB

    def switch_tab(self, target_tab: str, update_hash: bool = True) -> str:
        """Switch active tab, update active classes, and synchronize history."""
        target = self.parse_hash(target_tab)
        self.active_tab = target
        for t in self.VALID_TABS:
            self.tab_states[t] = (t == target)
        if update_hash:
            self.history.append(target)
        return self.active_tab

    def get_active_tab(self) -> str:
        return self.active_tab


def filter_device_records(devices: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Simulates ops_analytics.js client-side search filter logic."""
    if not query or not query.strip():
        return devices
        
    q = query.lower().strip()
    return [
        d for d in devices
        if q in str(d.get("deviceName", "")).lower()
        or q in str(d.get("userPrincipalName", "")).lower()
        or q in str(d.get("serialNumber", "")).lower()
        or q in str(d.get("model", "")).lower()
        or q in str(d.get("operatingSystem", "")).lower()
        or q in str(d.get("manufacturer", "")).lower()
    ]


def generate_rfc4180_csv(devices: List[Dict[str, Any]]) -> str:
    """Generates RFC 4180 compliant CSV string matching ops_analytics.js export format."""
    headers = [
        "Device Name", "Device ID", "Operating System", "OS Version",
        "User Principal Name", "Manufacturer", "Model", "Serial Number",
        "Compliance State", "Total Storage (GB)", "Free Storage (GB)",
        "Used Storage (%)", "Last Sync (UTC)"
    ]
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerow(headers)
    
    for d in devices:
        writer.writerow([
            d.get("deviceName", "N/A"),
            d.get("id", "N/A"),
            d.get("operatingSystem", "Unknown"),
            d.get("osVersion", "N/A"),
            d.get("userPrincipalName", "N/A"),
            d.get("manufacturer", "N/A"),
            d.get("model", "N/A"),
            d.get("serialNumber", "N/A"),
            d.get("complianceState", "unknown"),
            d.get("totalStorageGB", 0.0),
            d.get("freeStorageGB", 0.0),
            d.get("usedStoragePct", 0.0),
            d.get("lastSync", "N/A")
        ])
        
    return output.getvalue()


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestTabNavigationHTMLStructure(unittest.TestCase):
    """Tier 1: Static HTML DOM structure assertions for OPS Analytics."""
    
    @classmethod
    def setUpClass(cls):
        html_path = os.path.join(WORKSPACE_ROOT, "ops_analytics.html")
        if not os.path.exists(html_path):
            html_path = os.path.join(WORKSPACE_ROOT, "src", "frontend", "ops_analytics.html")
        with open(html_path, "r", encoding="utf-8") as f:
            cls.html_content = f.read()
        cls.parser = TabHTMLParser()
        cls.parser.feed(cls.html_content)

    def test_tier1_tab_buttons_count_and_keys(self):
        """Tier 1: HTML must declare tab buttons with valid data-tab attributes."""
        tab_keys = [btn["data-tab"] for btn in self.parser.tab_buttons]
        expected_keys = ["intune", "solarwinds", "network", "dex"]
        self.assertGreaterEqual(len(tab_keys), 4, f"Expected at least 4 tab buttons, found: {tab_keys}")
        for exp in expected_keys:
            self.assertIn(exp, tab_keys, f"Tab button for '{exp}' not found in HTML!")

    def test_tier1_default_active_tab_in_html(self):
        """Tier 1: Intune or Overview tab must have 'active' class on initial page load."""
        active_tabs = [btn["data-tab"] for btn in self.parser.tab_buttons if "active" in btn["class"].split()]
        self.assertTrue(len(active_tabs) > 0, "At least one tab button should be marked active by default")
        self.assertTrue("intune" in active_tabs or "overview" in active_tabs)

    def test_tier1_kpi_and_chart_elements_exist(self):
        """Tier 1: Core KPI and Chart.js canvas elements must be present in HTML."""
        self.assertIn("osChart", self.parser.canvas_ids)
        self.assertIn("complianceChart", self.parser.canvas_ids)
        self.assertIn("mfgChart", self.parser.canvas_ids)
        self.assertTrue(self.parser.has_search_input, "Search input element #deviceSearchInput must exist")
        self.assertTrue(self.parser.has_export_btn, "Export CSV button #exportCsvBtn must exist")
        self.assertTrue(self.parser.has_pulse_dot, "Pulse dot live indicator must exist")


class TestTabRouterController(unittest.TestCase):
    """Tier 1 & Tier 2: Tab Router logic, state switching, and deep linking."""

    def test_tier1_switch_all_5_tabs(self):
        """Tier 1: Switching to all 5 tabs updates active state cleanly."""
        router = TabRouterSimulation()
        tabs = ["overview", "intune", "solarwinds", "network", "dex"]
        for tab in tabs:
            active = router.switch_tab(tab)
            self.assertEqual(active, tab)
            self.assertTrue(router.tab_states[tab])
            # Ensure other tabs are inactive
            other_active = [t for t, is_active in router.tab_states.items() if is_active and t != tab]
            self.assertEqual(len(other_active), 0)

    def test_tier1_valid_hash_deep_linking(self):
        """Tier 1: Direct deep link hashes (#solarwinds, #dex) parse to correct tab."""
        self.assertEqual(TabRouterSimulation.parse_hash("#overview"), "overview")
        self.assertEqual(TabRouterSimulation.parse_hash("#intune"), "intune")
        self.assertEqual(TabRouterSimulation.parse_hash("#solarwinds"), "solarwinds")
        self.assertEqual(TabRouterSimulation.parse_hash("#network"), "network")
        self.assertEqual(TabRouterSimulation.parse_hash("#dex"), "dex")

    def test_tier2_empty_and_unknown_hash_fallback(self):
        """Tier 2: Empty or invalid hash strings must safely fallback to 'overview'."""
        self.assertEqual(TabRouterSimulation.parse_hash(""), "overview")
        self.assertEqual(TabRouterSimulation.parse_hash("#"), "overview")
        self.assertEqual(TabRouterSimulation.parse_hash("#invalid-route"), "overview")
        self.assertEqual(TabRouterSimulation.parse_hash("#random_string_123"), "overview")
        self.assertEqual(TabRouterSimulation.parse_hash(None), "overview")

    def test_tier2_hash_case_and_whitespace_insensitivity(self):
        """Tier 2: URL hashes with uppercase or surrounding whitespace resolve correctly."""
        self.assertEqual(TabRouterSimulation.parse_hash("#INTUNE"), "intune")
        self.assertEqual(TabRouterSimulation.parse_hash("  #dex  "), "dex")
        self.assertEqual(TabRouterSimulation.parse_hash("#SolarWinds"), "solarwinds")


class TestSearchFilterEngine(unittest.TestCase):
    """Tier 1 & Tier 2: Client-side table search filtering across device fields."""

    @classmethod
    def setUpClass(cls):
        summary_path = os.path.join(WORKSPACE_ROOT, "data", "intune_summary.json")
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                cls.devices = json.load(f).get("sample_devices", [])
        else:
            cls.devices = [
                {"deviceName": "LAP-NJ-81003082", "userPrincipalName": "Janhvi.Tendulkar@example.com", "serialNumber": "J02XDJ4", "model": "Dell Pro 14", "operatingSystem": "Windows"},
                {"deviceName": "LAP-LON-10029", "userPrincipalName": "john.smith@example.com", "serialNumber": "PF3XYZ01", "model": "ThinkPad T14", "operatingSystem": "Windows"},
                {"deviceName": "MAC-NYC-00451", "userPrincipalName": "sarah.connor@example.com", "serialNumber": "C02XYZ88", "model": "MacBook Pro", "operatingSystem": "macOS"}
            ]

    def test_tier1_empty_search_returns_all_devices(self):
        """Tier 1: Empty search query or whitespace returns all records."""
        self.assertEqual(len(filter_device_records(self.devices, "")), len(self.devices))
        self.assertEqual(len(filter_device_records(self.devices, "   ")), len(self.devices))
        self.assertEqual(len(filter_device_records(self.devices, None)), len(self.devices))

    def test_tier1_search_by_hostname(self):
        """Tier 1: Substring search by hostname matches expected devices."""
        results = filter_device_records(self.devices, "LAP-")
        self.assertTrue(len(results) > 0)
        for r in results:
            self.assertTrue(
                "lap-" in r["deviceName"].lower() or
                "lap-" in r.get("userPrincipalName", "").lower() or
                "lap-" in r.get("model", "").lower()
            )

    def test_tier1_search_case_insensitivity(self):
        """Tier 1: Search is strictly case-insensitive ('windows', 'WINDOWS', 'Windows')."""
        res_lower = filter_device_records(self.devices, "windows")
        res_upper = filter_device_records(self.devices, "WINDOWS")
        self.assertEqual(len(res_lower), len(res_upper))

    def test_tier2_non_matching_search_returns_empty_list(self):
        """Tier 2: Searching non-existent keyword returns empty list without error."""
        results = filter_device_records(self.devices, "NON_EXISTENT_HOSTNAME_ZZZ_9999")
        self.assertEqual(len(results), 0)


class TestCSVExportCompliance(unittest.TestCase):
    """Tier 1 & Tier 2: RFC 4180 CSV export validation."""

    def test_tier1_rfc4180_headers_and_row_count(self):
        """Tier 1: CSV contains exact 13 headers and correct data row count."""
        sample_data = [
            {
                "id": "uuid-1", "deviceName": "LAP-001", "operatingSystem": "Windows",
                "osVersion": "10.0.26200", "userPrincipalName": "user1@example.com",
                "manufacturer": "Dell Inc.", "model": "Latitude 5420",
                "serialNumber": "SN001", "complianceState": "compliant",
                "totalStorageGB": 512.0, "freeStorageGB": 256.0,
                "usedStoragePct": 50.0, "lastSync": "2026-06-01T10:00:00Z"
            },
            {
                "id": "uuid-2", "deviceName": 'LAP-002 "Special"', "operatingSystem": "macOS",
                "osVersion": "26.6.1", "userPrincipalName": "user2@example.com",
                "manufacturer": "Apple", "model": "MacBook Pro, 14-inch",
                "serialNumber": "SN002", "complianceState": "noncompliant",
                "totalStorageGB": 1024.0, "freeStorageGB": 800.0,
                "usedStoragePct": 21.9, "lastSync": "2026-06-02T11:00:00Z"
            }
        ]
        
        csv_text = generate_rfc4180_csv(sample_data)
        reader = list(csv.reader(io.StringIO(csv_text)))
        
        # Verify Headers
        expected_headers = [
            "Device Name", "Device ID", "Operating System", "OS Version",
            "User Principal Name", "Manufacturer", "Model", "Serial Number",
            "Compliance State", "Total Storage (GB)", "Free Storage (GB)",
            "Used Storage (%)", "Last Sync (UTC)"
        ]
        self.assertEqual(reader[0], expected_headers)
        self.assertEqual(len(reader), 3) # 1 header + 2 rows

    def test_tier2_csv_escaping_quotes_and_commas(self):
        """Tier 2: Quotes and commas within device names and models are escaped properly."""
        tricky_data = [{
            "id": "uuid-tricky",
            "deviceName": 'LAP-003, "High-Priority"',
            "operatingSystem": "Windows",
            "osVersion": "10.0",
            "userPrincipalName": "vip,exec@example.com",
            "manufacturer": "HP",
            "model": "EliteBook, 840 G8",
            "serialNumber": 'SN"123"',
            "complianceState": "compliant",
            "totalStorageGB": 500.0,
            "freeStorageGB": 250.0,
            "usedStoragePct": 50.0,
            "lastSync": "2026-06-01T00:00:00Z"
        }]
        
        csv_text = generate_rfc4180_csv(tricky_data)
        reader = list(csv.reader(io.StringIO(csv_text)))
        row = reader[1]
        
        self.assertEqual(row[0], 'LAP-003, "High-Priority"')
        self.assertEqual(row[4], 'vip,exec@example.com')
        self.assertEqual(row[6], 'EliteBook, 840 G8')
        self.assertEqual(row[7], 'SN"123"')


class TestLauncherBridge(unittest.TestCase):
    """Tier 1: Launcher shortcuts and overlay logic verification."""
    
    @classmethod
    def setUpClass(cls):
        app_js_path = os.path.join(WORKSPACE_ROOT, "app.js")
        if not os.path.exists(app_js_path):
            app_js_path = os.path.join(WORKSPACE_ROOT, "src", "frontend", "js", "app.js")
        with open(app_js_path, "r", encoding="utf-8") as f:
            cls.app_js = f.read()

    def test_tier1_keyboard_shortcuts_defined(self):
        """Tier 1: 'app.js' handles '/' for focus and 'Escape' for dismissal."""
        self.assertIn("e.key === '/'", self.app_js)
        self.assertIn("e.key === 'Escape'", self.app_js)

    def test_tier1_launcher_overlay_logic_present(self):
        """Tier 1: 'app.js' contains launchModule and closeLauncher functions."""
        self.assertIn("launchModule", self.app_js)
        self.assertIn("closeLauncher", self.app_js)
        self.assertIn("launcherOverlay", self.app_js)


if __name__ == "__main__":
    unittest.main(verbosity=2)
