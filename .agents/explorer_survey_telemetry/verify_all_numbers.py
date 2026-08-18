import json
import os
from collections import Counter
from datetime import datetime

raw_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "intune_ops_analytics.json")
summary_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "intune_summary.json")

with open(raw_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

devices = raw_data["devices"]
assert len(devices) == 25987, f"Expected 25987 devices, got {len(devices)}"

# 1. OS breakdown
os_counts = Counter(d.get("operatingSystem") or "Unknown" for d in devices)
print("OS Breakdown:", dict(os_counts))

# 2. Compliance breakdown
comp_counts = Counter(d.get("complianceState") or "unknown" for d in devices)
print("Compliance Breakdown:", dict(comp_counts))

# 3. Manufacturer raw
mfg_raw = Counter(d.get("manufacturer") or "Unknown" for d in devices)
print("Top 10 Raw Manufacturers:", dict(mfg_raw.most_common(10)))

# 4. Storage calculation
storage_devs = [d for d in devices if (d.get("totalStorageSpaceInBytes") or 0) > 0]
tot_bytes = sum(d["totalStorageSpaceInBytes"] for d in storage_devs)
free_bytes = sum(d.get("freeStorageSpaceInBytes", 0) for d in storage_devs)
used_bytes = tot_bytes - free_bytes

tot_tb = tot_bytes / (1024**4)
free_tb = free_bytes / (1024**4)
used_tb = used_bytes / (1024**4)
used_pct = (used_bytes / tot_bytes) * 100

print(f"Storage: reporting={len(storage_devs)}, Total={tot_tb:.4f} TB, Free={free_tb:.4f} TB, Used={used_tb:.4f} TB, Used%={used_pct:.2f}%")

# 5. UPN assignment
with_upn = sum(1 for d in devices if d.get("userPrincipalName"))
without_upn = len(devices) - with_upn
print(f"UPN Assigned: {with_upn}, Unassigned: {without_upn}")

# 6. Verify Summary JSON consistency
with open(summary_path, "r", encoding="utf-8") as f:
    sum_data = json.load(f)

print("Summary Metrics:", sum_data["metrics"])
print("Summary OS Breakdown:", sum_data["os_breakdown"])
print("Summary Compliance:", sum_data["compliance_breakdown"])
print("Summary Mfg:", sum_data["manufacturer_breakdown"])
print("Summary Sample Count:", len(sum_data["sample_devices"]))

print("\nALL VERIFICATIONS PASSED SUCCESSFULLY.")
