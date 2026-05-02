"""
SCRIPT 01 — Merge & Label
IoMT Monitoring System | MMM Ukasha IT22904232

What this does:
  - Loads all 4 sensor CSV files
  - Merges them into one master dataset
  - Assigns priority_label (CRITICAL / HIGH / MEDIUM / LOW)
  - Saves master dataset to data/raw/master_dataset.csv

Priority Rules:
  CRITICAL → life_support=TRUE (ICU)
              OR ddos on tier >= 7
              OR sensor_spoofing on life_support=TRUE
  HIGH     → life_support=FALSE AND tier >= 7
              OR ddos on tier < 7
              OR data_tampering any device
              OR device_identity_spoofing
  MEDIUM   → tier 5 or 6 with active attack
              OR mqtt_port_manipulation
              OR protocol_anomaly
              OR ip_spoofing
  LOW      → normal traffic (is_attack=FALSE)
              OR flooding on non-life-support
"""

import pandas as pd
import os

print("=" * 65)
print("  SCRIPT 01 — MERGE ALL SENSORS & ASSIGN PRIORITY LABELS")
print("=" * 65)

# ── Paths ────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW    = os.path.join(BASE, "data", "raw")
OUTPUT = os.path.join(RAW, "master_dataset.csv")

# ── Load each sensor file ────────────────────────────────────────
COMMON_COLS = [
    "timestamp", "device_id", "device_type", "ward",
    "life_support", "criticality_tier", "protocol",
    "src_ip", "dst_port", "attack_type", "is_attack"
]

files = {
    "temperature": os.path.join(RAW, "temperature_sensor_log.csv"),
    "pulse":       os.path.join(RAW, "pulse_oximeter_log.csv"),
    "motion":      os.path.join(RAW, "motion_sensor_log.csv"),
    "ecg":         os.path.join(RAW, "ecg_sensor_log.csv"),
}

frames = []
for name, path in files.items():
    df = pd.read_csv(path)
    df = df[COMMON_COLS]   # keep only common columns
    df["sensor_source"] = name
    frames.append(df)
    print(f"  Loaded {name:12s}: {len(df):>4} rows")

master = pd.concat(frames, ignore_index=True)
print(f"\n  Total rows after merge: {len(master)}")

# ── Encode helpers ───────────────────────────────────────────────
master["life_support_bool"] = master["life_support"].astype(str).str.upper() == "TRUE"
master["is_attack_bool"]    = master["is_attack"].astype(str).str.upper()    == "TRUE"
master["criticality_tier"]  = master["criticality_tier"].astype(int)

# ── Assign priority_label ────────────────────────────────────────
def assign_priority(row):
    ls   = row["life_support_bool"]
    tier = row["criticality_tier"]
    atk  = row["attack_type"]
    is_a = row["is_attack_bool"]

    # ── CRITICAL ─────────────────────────────────────────────────
    if ls and is_a:
        return "CRITICAL"
    if atk == "ddos" and tier >= 7:
        return "CRITICAL"
    if atk == "sensor_spoofing" and ls:
        return "CRITICAL"

    # ── HIGH ─────────────────────────────────────────────────────
    if not ls and tier >= 7 and is_a:
        return "HIGH"
    if atk == "ddos" and tier < 7:
        return "HIGH"
    if atk == "data_tampering":
        return "HIGH"
    if atk == "device_identity_spoofing":
        return "HIGH"

    # ── MEDIUM ───────────────────────────────────────────────────
    if atk in ("mqtt_port_manipulation", "protocol_anomaly", "ip_spoofing"):
        return "MEDIUM"
    if atk == "sensor_spoofing" and not ls:
        return "MEDIUM"
    if atk == "flooding" and tier >= 7:
        return "MEDIUM"

    # ── LOW ──────────────────────────────────────────────────────
    return "LOW"

master["priority_label"] = master.apply(assign_priority, axis=1)

# ── Summary ──────────────────────────────────────────────────────
print("\n  Priority Label Distribution:")
counts = master["priority_label"].value_counts()
for label in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
    n   = counts.get(label, 0)
    pct = n / len(master) * 100
    print(f"    {label:<10}: {n:>4} rows  ({pct:.1f}%)")

# ── Save ─────────────────────────────────────────────────────────
master.drop(columns=["life_support_bool", "is_attack_bool"], inplace=True)
master.to_csv(OUTPUT, index=False)

print(f"\n  Saved → data/raw/master_dataset.csv  ({len(master)} rows)")
print("\n  ✅  SCRIPT 01 COMPLETE — Run 02_preprocess.py next")
print("=" * 65)