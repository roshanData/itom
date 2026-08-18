import json
import os
from collections import Counter
from datetime import datetime

data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
raw_path = os.path.join(data_dir, "intune_ops_analytics.json")
summary_path = os.path.join(data_dir, "intune_summary.json")

print("--- RAW DATASET ANALYSIS ---")
with open(raw_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

summary_in_raw = raw_data.get("summary", {})
devices = raw_data.get("devices", [])

print(f"Total devices in 'devices' array: {len(devices)}")
print(f"Summary total_devices: {summary_in_raw.get('total_devices')}")

# Fields present across device objects
all_keys = set()
key_presence = Counter()
os_counts = Counter()
os_version_counts = Counter()
compliance_counts = Counter()
mfg_raw_counts = Counter()
model_counts = Counter()
ownership_counts = Counter()
sync_dates = []

total_storage_devices = 0
total_storage_bytes = 0
free_storage_bytes = 0

null_or_empty = Counter()

for d in devices:
    for k in d.keys():
        all_keys.add(k)
        key_presence[k] += 1
        
    os_val = d.get("operatingSystem")
    os_counts[str(os_val)] += 1
    
    os_ver = d.get("osVersion")
    if os_ver:
        os_version_counts[str(os_ver)] += 1
        
    comp = d.get("complianceState")
    compliance_counts[str(comp)] += 1
    
    mfg = d.get("manufacturer")
    mfg_raw_counts[str(mfg)] += 1
    
    model = d.get("model")
    model_counts[str(model)] += 1
    
    # Check if ownership field exists under any name
    for k in ["managedDeviceOwnerType", "ownership", "deviceOwnership", "deviceCategoryDisplayName"]:
        if k in d:
            ownership_counts[f"{k}:{d[k]}"] += 1
            
    tot = d.get("totalStorageSpaceInBytes")
    free = d.get("freeStorageSpaceInBytes")
    if tot is not None and tot > 0:
        total_storage_devices += 1
        total_storage_bytes += tot
        if free is not None:
            free_storage_bytes += free
            
    sync = d.get("lastSyncDateTime")
    if sync:
        sync_dates.append(sync)
        
    for k, v in d.items():
        if v is None or v == "" or v == "Unknown" or v == "N/A":
            null_or_empty[k] += 1

print("\n--- SCHEMA / KEYS FOUND IN DEVICE OBJECTS ---")
for k, count in key_presence.items():
    print(f"  {k}: {count} / {len(devices)} ({(count/len(devices))*100:.2f}%)")

print("\n--- OS BREAKDOWN ---")
for k, count in os_counts.most_common():
    print(f"  {k}: {count} ({(count/len(devices))*100:.2f}%)")

print("\n--- COMPLIANCE BREAKDOWN ---")
for k, count in compliance_counts.most_common():
    print(f"  {k}: {count} ({(count/len(devices))*100:.2f}%)")

print("\n--- TOP 15 MANUFACTURERS (RAW) ---")
for k, count in mfg_raw_counts.most_common(15):
    print(f"  {k}: {count} ({(count/len(devices))*100:.2f}%)")

# Categorized manufacturer breakdown
mfg_cat = Counter()
for d in devices:
    mfg = (d.get("manufacturer") or "").lower()
    if "dell" in mfg:
        mfg_cat["Dell"] += 1
    elif "hp" in mfg or "hewlett" in mfg:
        mfg_cat["HP"] += 1
    elif "lenovo" in mfg:
        mfg_cat["Lenovo"] += 1
    elif "apple" in mfg:
        mfg_cat["Apple"] += 1
    elif "microsoft" in mfg:
        mfg_cat["Microsoft"] += 1
    elif "samsung" in mfg:
        mfg_cat["Samsung"] += 1
    elif mfg == "" or mfg == "unknown" or mfg == "none":
        mfg_cat["Unknown/Empty"] += 1
    else:
        mfg_cat["Other"] += 1

print("\n--- CATEGORIZED MANUFACTURER BREAKDOWN ---")
for k, count in mfg_cat.most_common():
    print(f"  {k}: {count} ({(count/len(devices))*100:.2f}%)")

print("\n--- TOP 10 MODELS ---")
for k, count in model_counts.most_common(10):
    print(f"  {k}: {count} ({(count/len(devices))*100:.2f}%)")

print("\n--- OWNERSHIP DATA ---")
if ownership_counts:
    for k, count in ownership_counts.most_common():
        print(f"  {k}: {count}")
else:
    print("  No explicit ownership field (e.g. managedDeviceOwnerType) found in the selected Graph API fields.")

print("\n--- STORAGE UTILIZATION STATS ---")
print(f"Devices with storage reported: {total_storage_devices} / {len(devices)}")
if total_storage_devices > 0:
    tot_tb = total_storage_bytes / (1024**4)
    free_tb = free_storage_bytes / (1024**4)
    used_tb = tot_tb - free_tb
    used_pct = (used_tb / tot_tb) * 100
    print(f"Total Storage: {tot_tb:.2f} TB")
    print(f"Free Storage: {free_tb:.2f} TB")
    print(f"Used Storage: {used_tb:.2f} TB")
    print(f"Fleet Storage Used %: {used_pct:.2f}%")

print("\n--- SYNC DATES STATS ---")
print(f"Devices with lastSyncDateTime: {len(sync_dates)}")
if sync_dates:
    min_sync = min(sync_dates)
    max_sync = max(sync_dates)
    print(f"Earliest sync: {min_sync}")
    print(f"Latest sync: {max_sync}")

print("\n--- NULL / MISSING FIELD ANALYSIS ---")
for k, count in null_or_empty.items():
    print(f"  {k} null/empty/unknown: {count} ({(count/len(devices))*100:.2f}%)")

print("\n--- SUMMARY JSON INSPECTION ---")
with open(summary_path, "r", encoding="utf-8") as f:
    sum_data = json.load(f)

print("Summary keys:", list(sum_data.keys()))
print("Metrics in summary:", json.dumps(sum_data.get("metrics"), indent=2))
print("OS breakdown in summary:", json.dumps(sum_data.get("os_breakdown"), indent=2))
print("Compliance breakdown in summary:", json.dumps(sum_data.get("compliance_breakdown"), indent=2))
print("Manufacturer breakdown in summary:", json.dumps(sum_data.get("manufacturer_breakdown"), indent=2))
print(f"Sample devices count in summary: {len(sum_data.get('sample_devices', []))}")
