#!/usr/bin/env python3
"""SolarWinds Orion SWIS Deep Architecture & Telemetry Research Script (Refined).

STRICTLY READ-ONLY execution of SWQL queries across all Orion modules.
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SWISResearch")

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

host = os.getenv("SOLARWINDS_HOST", "gnoc.coforge.com")
port = os.getenv("SOLARWINDS_PORT", "17774")
username = os.getenv("SOLARWINDS_USERNAME")
password = os.getenv("SOLARWINDS_PASSWORD")

if not username or not password:
    logger.error("SolarWinds credentials missing in .env")
    sys.exit(1)

url = f"https://{host}:{port}/SolarWinds/InformationService/v3/Json/Query"

def swql_query(query: str, description: str = "") -> dict:
    """Execute a strictly read-only SWQL query."""
    clean_query = " ".join(query.strip().split())
    logger.info("Executing SWQL: %s | %s", description or "Query", clean_query[:90])
    try:
        resp = requests.get(
            url,
            params={"query": clean_query},
            auth=(username, password),
            timeout=30,
            verify=False
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            logger.info("-> Success: %d rows returned", len(results))
            return {"success": True, "count": len(results), "results": results, "error": None}
        else:
            logger.warning("-> Error %d: %s", resp.status_code, resp.text[:200])
            return {"success": False, "count": 0, "results": [], "error": resp.text, "status_code": resp.status_code}
    except Exception as e:
        logger.error("-> Exception: %s", str(e))
        return {"success": False, "count": 0, "results": [], "error": str(e)}

research_report = {
    "metadata": {
        "host": host,
        "port": port,
        "username": username,
        "endpoint": url
    },
    "data": {}
}

# 1. Metadata Schema Exploration
research_report["data"]["entities_orion_cirrus"] = swql_query(
    "SELECT EntityType, Name FROM Metadata.Entity WHERE Name LIKE 'Orion%' OR Name LIKE 'Cirrus%'",
    "Discovered Orion & Cirrus Entities"
)

research_report["data"]["all_namespaces"] = swql_query(
    "SELECT DISTINCT SUBSTRING(Name, 1, CHARINDEX('.', Name) - 1) AS Namespace FROM Metadata.Entity",
    "All Metadata Namespaces"
)

# 2. Nodes Infrastructure
research_report["data"]["nodes_total_count"] = swql_query(
    "SELECT COUNT(1) AS TotalNodes FROM Orion.Nodes",
    "Total Nodes Count"
)

research_report["data"]["nodes_status_distribution"] = swql_query(
    "SELECT Status, StatusDescription, COUNT(1) AS NodeCount FROM Orion.Nodes GROUP BY Status, StatusDescription ORDER BY NodeCount DESC",
    "Nodes Status Distribution"
)

research_report["data"]["nodes_by_vendor"] = swql_query(
    "SELECT Vendor, COUNT(1) AS NodeCount FROM Orion.Nodes GROUP BY Vendor ORDER BY NodeCount DESC",
    "Nodes by Vendor Breakdown"
)

research_report["data"]["nodes_top_cpu_memory"] = swql_query(
    "SELECT TOP 15 NodeID, Caption, IPAddress, Status, StatusDescription, CPULoad, PercentMemoryUsed, TotalMemory, ResponseTime, PercentLoss, MachineType, Vendor, LastSync FROM Orion.Nodes ORDER BY CPULoad DESC",
    "Top 15 High CPU/Memory Nodes"
)

research_report["data"]["nodes_problem_down"] = swql_query(
    "SELECT TOP 20 NodeID, Caption, IPAddress, Status, StatusDescription, ResponseTime, PercentLoss, LastSync, MachineType, Vendor FROM Orion.Nodes WHERE Status != 1 ORDER BY Status DESC",
    "Non-Up Nodes (Down, Warning, Critical, Unmanaged)"
)

# 3. Alerting & Incident Telemetry
research_report["data"]["alerts_active_count"] = swql_query(
    "SELECT COUNT(1) AS ActiveAlertCount FROM Orion.AlertActive",
    "Active Alert Total Count"
)

research_report["data"]["alerts_active_details"] = swql_query(
    """SELECT TOP 30 
        a.AlertActiveID, 
        a.AlertObjectID, 
        a.TriggeredDateTime, 
        a.Acknowledged,
        a.AcknowledgedBy,
        o.EntityCaption, 
        o.EntityType, 
        o.EntityNetObjectId, 
        ac.Name AS AlertName, 
        ac.Severity, 
        ac.Description 
    FROM Orion.AlertActive a 
    LEFT JOIN Orion.AlertObjects o ON a.AlertObjectID = o.AlertObjectID 
    LEFT JOIN Orion.AlertConfigurations ac ON o.AlertID = ac.AlertID 
    ORDER BY a.TriggeredDateTime DESC""",
    "Top 30 Active Alerts Details"
)

research_report["data"]["alerts_by_severity"] = swql_query(
    """SELECT ac.Severity, COUNT(1) AS AlertCount 
    FROM Orion.AlertActive a 
    LEFT JOIN Orion.AlertObjects o ON a.AlertObjectID = o.AlertObjectID 
    LEFT JOIN Orion.AlertConfigurations ac ON o.AlertID = ac.AlertID 
    GROUP BY ac.Severity""",
    "Active Alerts Grouped by Severity"
)

research_report["data"]["alerts_by_name"] = swql_query(
    """SELECT ac.Name AS AlertName, COUNT(1) AS TriggerCount 
    FROM Orion.AlertActive a 
    LEFT JOIN Orion.AlertObjects o ON a.AlertObjectID = o.AlertObjectID 
    LEFT JOIN Orion.AlertConfigurations ac ON o.AlertID = ac.AlertID 
    GROUP BY ac.Name 
    ORDER BY TriggerCount DESC""",
    "Active Alerts Grouped by Alert Definition"
)

# 4. Network Performance Monitor (NPM) - Interfaces
research_report["data"]["interfaces_total_count"] = swql_query(
    "SELECT COUNT(1) AS TotalInterfaces FROM Orion.NPM.Interfaces",
    "Total Interfaces Count"
)

research_report["data"]["interfaces_status_distribution"] = swql_query(
    "SELECT Status, COUNT(1) AS InterfaceCount FROM Orion.NPM.Interfaces GROUP BY Status ORDER BY InterfaceCount DESC",
    "Interfaces Status Distribution"
)

research_report["data"]["interfaces_type_distribution"] = swql_query(
    "SELECT TypeDescription, COUNT(1) AS TypeCount FROM Orion.NPM.Interfaces GROUP BY TypeDescription ORDER BY TypeCount DESC",
    "Interfaces by Type Description"
)

research_report["data"]["interfaces_top_utilization"] = swql_query(
    """SELECT TOP 20 
        i.InterfaceID, 
        i.NodeID, 
        i.Caption, 
        i.Status, 
        i.InPercentUtil, 
        i.OutPercentUtil, 
        i.InBps, 
        i.OutBps, 
        i.Speed, 
        n.Caption AS NodeCaption 
    FROM Orion.NPM.Interfaces i 
    LEFT JOIN Orion.Nodes n ON i.NodeID = n.NodeID 
    ORDER BY i.InPercentUtil DESC""",
    "Top 20 Utilized Interfaces"
)

research_report["data"]["interfaces_errors_discards"] = swql_query(
    """SELECT TOP 15 
        i.InterfaceID, 
        i.NodeID, 
        i.Caption, 
        i.Status, 
        i.InErrorsThisHour, 
        i.OutErrorsThisHour, 
        i.InDiscardsThisHour, 
        i.OutDiscardsThisHour, 
        n.Caption AS NodeCaption 
    FROM Orion.NPM.Interfaces i 
    LEFT JOIN Orion.Nodes n ON i.NodeID = n.NodeID 
    WHERE (i.InErrorsThisHour > 0 OR i.OutErrorsThisHour > 0 OR i.InDiscardsThisHour > 0 OR i.OutDiscardsThisHour > 0) 
    ORDER BY (i.InErrorsThisHour + i.OutErrorsThisHour + i.InDiscardsThisHour + i.OutDiscardsThisHour) DESC""",
    "Interfaces with Errors or Discards"
)

# 5. Storage Volumes
research_report["data"]["volumes_total_count"] = swql_query(
    "SELECT COUNT(1) AS TotalVolumes FROM Orion.Volumes",
    "Total Storage Volumes Count"
)

research_report["data"]["volumes_by_type"] = swql_query(
    "SELECT VolumeType, COUNT(1) AS VolumeCount, AVG(VolumePercentUsed) AS AvgUsed FROM Orion.Volumes GROUP BY VolumeType ORDER BY VolumeCount DESC",
    "Volumes by Type and Avg Utilization"
)

research_report["data"]["volumes_status_distribution"] = swql_query(
    "SELECT Status, COUNT(1) AS VolumeCount FROM Orion.Volumes GROUP BY Status ORDER BY VolumeCount DESC",
    "Volumes Status Distribution"
)

research_report["data"]["volumes_top_critical"] = swql_query(
    """SELECT TOP 25 
        v.VolumeID, 
        v.NodeID, 
        v.Caption, 
        v.VolumeType, 
        v.VolumeSize, 
        v.VolumeSpaceUsed, 
        v.VolumeSpaceAvailable, 
        v.VolumePercentUsed, 
        v.Status, 
        n.Caption AS NodeCaption 
    FROM Orion.Volumes v 
    LEFT JOIN Orion.Nodes n ON v.NodeID = n.NodeID 
    ORDER BY v.VolumePercentUsed DESC""",
    "Top 25 Highest Storage Consumption Volumes"
)

# 6. SAM / APM Applications
research_report["data"]["apm_applications_summary"] = swql_query(
    "SELECT Status, COUNT(1) AS AppCount FROM Orion.APM.Application GROUP BY Status ORDER BY AppCount DESC",
    "APM Applications Status Distribution"
)

research_report["data"]["apm_applications_sample"] = swql_query(
    """SELECT TOP 25 
        a.ApplicationID, 
        a.NodeID, 
        a.Name, 
        a.Status, 
        a.StatusDescription, 
        a.Unmanaged, 
        n.Caption AS NodeCaption 
    FROM Orion.APM.Application a 
    LEFT JOIN Orion.Nodes n ON a.NodeID = n.NodeID 
    ORDER BY a.Status DESC""",
    "APM Applications Sample"
)

research_report["data"]["apm_components_summary"] = swql_query(
    "SELECT Status, COUNT(1) AS ComponentCount FROM Orion.APM.Component GROUP BY Status ORDER BY ComponentCount DESC",
    "APM Components Status Distribution"
)

# 7. NCM / Cirrus (Network Configuration Manager)
research_report["data"]["cirrus_nodes_count"] = swql_query(
    "SELECT COUNT(1) AS NCMNodeCount FROM Cirrus.Nodes",
    "NCM Cirrus.Nodes Count"
)

research_report["data"]["cirrus_nodes_sample"] = swql_query(
    "SELECT TOP 10 NodeID, AgentIP, NodeCaption, Vendor, SysDescr FROM Cirrus.Nodes",
    "Cirrus Nodes Sample"
)

research_report["data"]["cirrus_configs_sample"] = swql_query(
    "SELECT TOP 10 ConfigID, NodeID, ConfigType, DownloadTime, AttemptedDownloadTime FROM Cirrus.ConfigArchive ORDER BY DownloadTime DESC",
    "Cirrus Config Archive Sample"
)

# 8. Virtualization (VMAN / VIM)
research_report["data"]["vim_vm_count"] = swql_query(
    "SELECT COUNT(1) AS VMCount FROM Orion.VIM.VirtualMachines",
    "VIM Virtual Machines Count"
)

research_report["data"]["vim_vms_sample"] = swql_query(
    """SELECT TOP 15 
        VirtualMachineID, 
        NodeID, 
        Name, 
        IPAddress, 
        MemoryConfigured, 
        ProcessorCount, 
        PowerState, 
        CpuLoad,
        MemUsage,
        Status 
    FROM Orion.VIM.VirtualMachines 
    ORDER BY MemoryConfigured DESC""",
    "VIM Virtual Machines Sample"
)

research_report["data"]["vim_hosts_count"] = swql_query(
    "SELECT COUNT(1) AS HostCount FROM Orion.VIM.Hosts",
    "VIM Hosts Count"
)

research_report["data"]["vim_hosts_sample"] = swql_query(
    "SELECT TOP 10 HostID, NodeID, HostName, IPAddress, CpuCoreCount, MemorySize, HostStatus, Status FROM Orion.VIM.Hosts",
    "VIM Hosts Sample"
)

# 9. Additional module checks (IPAM, UDT, NetPath, Events)
research_report["data"]["events_top"] = swql_query(
    """SELECT TOP 15 
        EventID, 
        EventTime, 
        EventType, 
        Message, 
        NetObjectID, 
        NetObjectType 
    FROM Orion.Events 
    ORDER BY EventTime DESC""",
    "Recent Orion Events Telemetry"
)

research_report["data"]["ipam_subnets_check"] = swql_query(
    "SELECT COUNT(1) AS SubnetCount FROM IPAM.Subnet",
    "IPAM Subnets Check"
)

research_report["data"]["udt_ports_check"] = swql_query(
    "SELECT COUNT(1) AS PortCount FROM Orion.UDT.Port",
    "UDT Ports Check"
)

# Save results
out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "solarwinds_deep_research.json")

with open(out_file, "w") as f:
    json.dump(research_report, f, indent=2, default=str)

logger.info("Refined research report successfully written to %s", out_file)
