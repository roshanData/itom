import json
import os
from collections import Counter
from datetime import datetime

data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
raw_path = os.path.join(data_dir, "intune_ops_analytics.json")

with open(raw_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

devices = raw_data.get("devices", [])

# Group by OS and OS Version
os_ver_map = {}
for d in devices:
    os_name = d.get("operatingSystem") or "Unknown"
    ver = d.get("osVersion") or "Unknown"
    if os_name not in os_ver_map:
        os_ver_map[os_name] = Counter()
    os_ver_map[os_name][ver] += 1

print("=== OS AND OS VERSION BREAKDOWN ===")
for os_name, ver_counter in sorted(os_ver_map.items(), key=lambda x: -sum(x[1].values())):
    total_os = sum(ver_counter.values())
    print(f"\n{os_name}: {total_os} total ({(total_os/len(devices))*100:.2f}%)")
    for ver, count in ver_counter.most_common(8):
        print(f"   - {ver}: {count} ({(count/total_os)*100:.2f}%)")

# Compliance breakdown by OS
print("\n=== COMPLIANCE BREAKDOWN BY OS ===")
comp_by_os = {}
for d in devices:
    os_name = d.get("operatingSystem") or "Unknown"
    comp = d.get("complianceState") or "unknown"
    if os_name not in comp_by_os:
        comp_by_os[os_name] = Counter()
    comp_by_os[os_name][comp] += 1

for os_name, comp_counter in sorted(comp_by_os.items(), key=lambda x: -sum(x[1].values())):
    print(f"\n{os_name} (Total {sum(comp_counter.values())}):")
    for comp, count in comp_counter.most_common():
        print(f"   - {comp}: {count} ({(count/sum(comp_counter.values()))*100:.2f}%)")

# Sync Recency Breakdown
print("\n=== SYNC RECENCY BREAKDOWN ===")
sync_buckets = Counter()
invalid_dates = 0

for d in devices:
    sync_str = d.get("lastSyncDateTime")
    if not sync_str or sync_str.startswith("0001"):
        sync_buckets["Never / Invalid (0001-01-01)"] += 1
        invalid_dates += 1
    else:
        try:
            dt = datetime.fromisoformat(sync_str.replace("Z", "+00:00"))
            # Reference time: 2026-08-17
            ref_dt = datetime.fromisoformat("2026-08-17T23:59:59+00:00")
            delta_days = (ref_dt - dt).days
            if delta_days <= 1:
                sync_buckets["< 24 Hours"] += 1
            elif delta_days <= 7:
                sync_buckets["1 - 7 Days"] += 1
            elif delta_days <= 30:
                sync_buckets["8 - 30 Days"] += 1
            elif delta_days <= 90:
                sync_buckets["31 - 90 Days"] += 1
            else:
                sync_buckets["> 90 Days (Stale)"] += 1
        except Exception as e:
            sync_buckets["Parse Error"] += 1

for bucket, count in sync_buckets.items():
    print(f"   - {bucket}: {count} ({(count/len(devices))*100:.2f}%)")

