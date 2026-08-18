import json
import os

with open("data/solarwinds_deep_research.json", "r") as f:
    data = json.load(f)["data"]

print("="*60)
print("SOLARWINDS ORION TELEMETRY & ARCHITECTURE SUMMARY")
print("="*60)

# 1. Nodes
total_nodes = data.get("nodes_total_count", {}).get("results", [{}])[0].get("TotalNodes", 0)
print(f"\n1. INFRASTRUCTURE NODES: Total = {total_nodes}")
print("Status Breakdown:")
for row in data.get("nodes_status_distribution", {}).get("results", []):
    print(f"  - Status {row.get('Status')} ({row.get('StatusDescription')}): {row.get('NodeCount')} nodes")

print("\nTop Vendors:")
for row in data.get("nodes_by_vendor", {}).get("results", [])[:8]:
    print(f"  - {row.get('Vendor') or 'Unknown'}: {row.get('NodeCount')} nodes")

# 2. Active Alerts
alert_count = data.get("alerts_active_count", {}).get("results", [{}])[0].get("ActiveAlertCount", 0)
print(f"\n2. ACTIVE ALERTS: Total Active = {alert_count}")
print("Severity Breakdown:")
severity_map = {0: "Informational", 1: "Warning", 2: "Critical", 3: "Serious"}
for row in data.get("alerts_by_severity", {}).get("results", []):
    sev = row.get("Severity")
    print(f"  - Severity {sev} ({severity_map.get(sev, 'Unknown')}): {row.get('AlertCount')} active alerts")

print("\nTop Active Alert Definitions:")
for row in data.get("alerts_by_name", {}).get("results", [])[:8]:
    print(f"  - {row.get('AlertName')}: {row.get('TriggerCount')} triggers")

# 3. Interfaces (NPM)
total_ifaces = data.get("interfaces_total_count", {}).get("results", [{}])[0].get("TotalInterfaces", 0)
print(f"\n3. NETWORK INTERFACES (NPM): Total = {total_ifaces}")
print("Interface Status Breakdown:")
if_status_map = {1: "Up", 2: "Down", 3: "Warning", 9: "Unmanaged", 24: "Administratively Down"}
for row in data.get("interfaces_status_distribution", {}).get("results", []):
    st = row.get("Status")
    print(f"  - Status {st} ({if_status_map.get(st, 'Other')}): {row.get('InterfaceCount')}")

# 4. Volumes
total_vols = data.get("volumes_total_count", {}).get("results", [{}])[0].get("TotalVolumes", 0)
print(f"\n4. STORAGE VOLUMES: Total = {total_vols}")
print("Volume Type Breakdown & Average Usage:")
for row in data.get("volumes_by_type", {}).get("results", []):
    avg_u = row.get('AvgUsed')
    avg_str = f"{avg_u:.1f}%" if avg_u is not None else "N/A"
    print(f"  - {row.get('VolumeType')}: {row.get('VolumeCount')} volumes, Avg Util = {avg_str}")

# 5. SAM / APM Applications
apm_count = sum(r.get("AppCount", 0) for r in data.get("apm_applications_summary", {}).get("results", []))
print(f"\n5. APPLICATIONS (SAM / APM): Total Applications = {apm_count}")
for row in data.get("apm_applications_summary", {}).get("results", []):
    print(f"  - Status {row.get('Status')}: {row.get('AppCount')} applications")

comp_count = sum(r.get("ComponentCount", 0) for r in data.get("apm_components_summary", {}).get("results", []))
print(f"   Total Component Monitors = {comp_count}")

# 6. Virtualization (VMAN / VIM)
vm_count = data.get("vim_vm_count", {}).get("results", [{}])[0].get("VMCount", 0)
host_count = data.get("vim_hosts_count", {}).get("results", [{}])[0].get("HostCount", 0)
print(f"\n6. VIRTUALIZATION (VMAN / VIM): Total VMs = {vm_count}, Total Hypervisor Hosts = {host_count}")

# 7. NCM / Cirrus
ncm_count = data.get("cirrus_nodes_count", {}).get("results", [{}])[0].get("NCMNodeCount", 0)
print(f"\n7. NETWORK CONFIGURATION (NCM / CIRRUS): Managed NCM Nodes = {ncm_count}")

# 8. IPAM & UDT
subnet_count = data.get("ipam_subnets_check", {}).get("results", [{}])[0].get("SubnetCount", 0)
port_count = data.get("udt_ports_check", {}).get("results", [{}])[0].get("PortCount", 0)
print(f"\n8. IPAM & UDT: Subnets Managed = {subnet_count}, Switch Ports Monitored = {port_count}")
