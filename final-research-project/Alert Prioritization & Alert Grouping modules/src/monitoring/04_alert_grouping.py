"""
SCRIPT 04 — Alert Grouping (Novelty 2)
IoMT Monitoring System | MMM Ukasha IT22904232

What this does:
  - Loads master_dataset.csv + priority labels from model predictions
  - Groups related alerts into incidents using 3 rules:
      1. Temporal  — same src_ip, alerts within 30s window
      2. Device    — same ward, alerts within 60s window
      3. Attack    — same attack_type across devices (coordinated)
  - Uses DBSCAN clustering on (timestamp + src_ip + attack_type)
  - Shows: how many alerts → how many grouped incidents
  - Saves grouped_incidents.csv → data/processed/
  - Saves grouping charts → results/
"""

import pandas as pd
import numpy as np
import os
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from sklearn.cluster import DBSCAN

print("=" * 65)
print("  SCRIPT 04 — ALERT GROUPING  (NOVELTY 2)")
print("=" * 65)

# ── Paths ────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_PATH = os.path.join(BASE, "data", "raw",       "master_dataset.csv")
PROC_DIR = os.path.join(BASE, "data", "processed")
RES_DIR  = os.path.join(BASE, "results")
MDL_DIR  = os.path.join(BASE, "models")
os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(RES_DIR,  exist_ok=True)

# ── Load master dataset ───────────────────────────────────────────
df = pd.read_csv(RAW_PATH)
print(f"\n  Loaded master_dataset.csv: {len(df)} rows")

# Keep only attack rows for grouping (normal traffic is not grouped)
attacks = df[df["is_attack"].astype(str).str.upper() == "TRUE"].copy().reset_index(drop=True)
print(f"  Attack rows to group: {len(attacks)}")

# ── Load model to predict priority for each alert ─────────────────
with open(os.path.join(MDL_DIR, "alert_prioritization_model.pkl"), "rb") as f:
    model = pickle.load(f)
with open(os.path.join(MDL_DIR, "feature_names.pkl"), "rb") as f:
    feature_names = pickle.load(f)
with open(os.path.join(MDL_DIR, "label_encoders.pkl"), "rb") as f:
    encoders = pickle.load(f)

# ── Re-encode attack rows with same encoders ──────────────────────
attacks["life_support_int"] = (attacks["life_support"].astype(str).str.upper() == "TRUE").astype(int)
attacks["is_attack_int"]    = 1

for col in ["device_type","ward","protocol","attack_type","sensor_source"]:
    le = encoders[col]
    attacks[col + "_enc"] = attacks[col].apply(
        lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
    )

attacks["is_icu"]              = (attacks["ward"] == "ICU").astype(int)
attacks["is_port_anomaly"]     = (attacks["dst_port"] != 1883).astype(int)
attacks["is_unknown_device"]   = attacks["device_id"].str.contains(
                                    "UNKNOWN|ROGUE|FAKE|GHOST|CLONE",
                                    case=False, na=False).astype(int)
attacks["is_protocol_anomaly"] = (~attacks["protocol"].isin(["MQTT","BLE_MQTT"])).astype(int)

X_attacks = attacks[feature_names]
attacks["predicted_priority"] = model.predict(X_attacks)

# ── DBSCAN Grouping ───────────────────────────────────────────────
# Normalize features for clustering
ip_le  = LabelEncoder().fit(attacks["src_ip"])
atk_le = LabelEncoder().fit(attacks["attack_type"])

cluster_input = np.column_stack([
    attacks["timestamp"].values / attacks["timestamp"].max(),       # time
    ip_le.transform(attacks["src_ip"]) / len(ip_le.classes_),       # src ip
    atk_le.transform(attacks["attack_type"]) / len(atk_le.classes_),# attack type
    attacks["ward_enc"].values / attacks["ward_enc"].max(),          # ward
])

db = DBSCAN(eps=0.08, min_samples=2, metric="euclidean")
attacks["group_id"] = db.fit_predict(cluster_input)

# ── Build grouped incident summary ───────────────────────────────
total_alerts   = len(attacks)
noise_mask     = attacks["group_id"] == -1
grouped        = attacks[~noise_mask]
ungrouped      = attacks[noise_mask]
n_groups       = grouped["group_id"].nunique()

print(f"\n  Grouping Results:")
print(f"    Total attack alerts  : {total_alerts}")
print(f"    Grouped into clusters: {n_groups} incident groups")
print(f"    Standalone alerts    : {len(ungrouped)}")
reduction = (1 - (n_groups + len(ungrouped)) / total_alerts) * 100
print(f"    Alert reduction      : {reduction:.1f}%")

# ── Incident summary table ────────────────────────────────────────
incidents = []
for gid, grp in grouped.groupby("group_id"):
    incidents.append({
        "incident_id"        : f"INC-{gid:04d}",
        "group_id"           : gid,
        "alert_count"        : len(grp),
        "attack_types"       : ", ".join(grp["attack_type"].unique()),
        "wards_affected"     : ", ".join(grp["ward"].unique()),
        "devices_affected"   : ", ".join(grp["device_id"].unique()),
        "src_ips"            : ", ".join(grp["src_ip"].unique()),
        "max_priority"       : grp["predicted_priority"].map(
                                   {"CRITICAL":4,"HIGH":3,"MEDIUM":2,"LOW":1}
                               ).idxmax() if len(grp) > 0 else "LOW",
        "incident_priority"  : grp["predicted_priority"].value_counts().idxmax(),
        "life_support_involved": grp["life_support"].astype(str).str.upper().eq("TRUE").any(),
        "start_timestamp"    : grp["timestamp"].min(),
        "end_timestamp"      : grp["timestamp"].max(),
    })

incident_df = pd.DataFrame(incidents)
print(f"\n  Sample Incident Groups:")
print(incident_df[["incident_id","alert_count","attack_types",
                   "wards_affected","incident_priority"]].head(10).to_string(index=False))

# ── Chart 1: Group size distribution ──────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
group_sizes = grouped["group_id"].value_counts().values
ax.hist(group_sizes, bins=10, color="#1f77b4", edgecolor="black")
ax.set_title("Alert Group Size Distribution\n(Alert Grouping — Novelty 2 | Ukasha IT22904232)",
             fontsize=11, fontweight="bold")
ax.set_xlabel("Alerts per Group"); ax.set_ylabel("Number of Groups")
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, "06_group_size_distribution.png"), dpi=150)
plt.close()
print("\n  Saved → results/06_group_size_distribution.png")

# ── Chart 2: Incidents by ward ────────────────────────────────────
ward_counts = attacks[~noise_mask]["ward"].value_counts()
colors_ward = ["#d62728","#ff7f0e","#2ca02c","#1f77b4"]
fig, ax = plt.subplots(figsize=(7, 4))
ward_counts.plot(kind="bar", ax=ax, color=colors_ward[:len(ward_counts)], edgecolor="black")
ax.set_title("Grouped Incidents by Ward\n(Which ward is most attacked?)",
             fontsize=11, fontweight="bold")
ax.set_xlabel("Ward"); ax.set_ylabel("Alert Count"); ax.tick_params(rotation=15)
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, "07_incidents_by_ward.png"), dpi=150)
plt.close()
print("  Saved → results/07_incidents_by_ward.png")

# ── Chart 3: Priority of grouped incidents ────────────────────────
order  = ["CRITICAL","HIGH","MEDIUM","LOW"]
c_map  = {"CRITICAL":"#d62728","HIGH":"#ff7f0e","MEDIUM":"#2ca02c","LOW":"#1f77b4"}
if len(incident_df) > 0:
    pri_counts = incident_df["incident_priority"].value_counts().reindex(order, fill_value=0)
    fig, ax = plt.subplots(figsize=(7, 4))
    pri_counts.plot(kind="bar", ax=ax, color=[c_map[l] for l in order], edgecolor="black")
    ax.set_title("Incident Priority After Grouping\n(Novelties 1+2 Combined)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Priority"); ax.set_ylabel("Incidents"); ax.tick_params(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(RES_DIR, "08_incident_priority.png"), dpi=150)
    plt.close()
    print("  Saved → results/08_incident_priority.png")

# ── Save outputs ──────────────────────────────────────────────────
attacks.to_csv(os.path.join(PROC_DIR, "grouped_alerts.csv"), index=False)
incident_df.to_csv(os.path.join(PROC_DIR, "grouped_incidents.csv"), index=False)

# Save text summary
with open(os.path.join(RES_DIR, "04_alert_grouping_summary.txt"), "w") as f:
    f.write("IoMT Alert Grouping Summary — Novelty 2\n")
    f.write("Student: MMM Ukasha  IT22904232\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Total attack alerts   : {total_alerts}\n")
    f.write(f"Incident groups formed: {n_groups}\n")
    f.write(f"Standalone alerts     : {len(ungrouped)}\n")
    f.write(f"Alert reduction       : {reduction:.1f}%\n\n")
    f.write("Incident Groups:\n")
    f.write(incident_df.to_string(index=False))

print("\n  Saved → data/processed/grouped_alerts.csv")
print("  Saved → data/processed/grouped_incidents.csv")
print("  Saved → results/04_alert_grouping_summary.txt")
print(f"\n  📊  {total_alerts} alerts → {n_groups} grouped incidents")
print(f"  📉  Alert reduction: {reduction:.1f}%")
print("\n  ✅  SCRIPT 04 COMPLETE — Run 05_demo.py next")
print("=" * 65)