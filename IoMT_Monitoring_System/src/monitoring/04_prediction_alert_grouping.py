"""
SCRIPT 04 - Prediction Alert Grouping
IoMT Monitoring System | MMM Ukasha IT22904232

This version groups stored prediction records instead of raw telemetry.
It builds prediction-driven incident clusters from the MongoDB predictions
collection, then writes grouped_alerts.csv and grouped_incidents.csv for the
Alert Grouping page.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_PATH = os.path.join(BASE, "data", "raw", "master_dataset.csv")
PROC_DIR = os.path.join(BASE, "data", "processed")
RES_DIR = os.path.join(BASE, "results")
os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

WINDOW_MS = 60_000
SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
CATEGORY_PRIORITY = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "attack": "MEDIUM",
    "normal": "LOW",
}


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return default


def _to_epoch_ms(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        raw = float(value)
        return int(raw if raw > 10_000_000_000 else raw * 1000)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            raw = float(text)
            return int(raw if raw > 10_000_000_000 else raw * 1000)
        except ValueError:
            pass
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return int(parsed.timestamp() * 1000)
        except ValueError:
            return None
    return None


def _normalize_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _split_joined_values(values: Iterable[Any]) -> str:
    seen: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text.lower() == "nan":
            continue
        parts = [part.strip() for part in text.split(",")]
        for part in parts:
            if part and part not in seen:
                seen.append(part)
    return ", ".join(seen)


def _priority_label(row: pd.Series) -> str:
    priority = str(row.get("priority", "LOW") or "LOW").upper()
    predicted_attack = _as_bool(row.get("predicted_attack", False))
    confirmed_real_attack = _as_bool(row.get("confirmed_real_attack", False))
    confirmed_critical = _as_bool(row.get("confirmed_critical", False))
    decision_action = str(row.get("decision_action", "") or "").lower()
    attack_label = str(row.get("attack_label", "") or "").upper()

    if priority == "CRITICAL" or confirmed_critical:
        return "critical"
    if priority == "HIGH":
        return "high"
    if predicted_attack or confirmed_real_attack or attack_label == "ATTACK" or decision_action in {"temporary_isolate", "quarantine", "shutdown", "rollback"} or priority == "MEDIUM":
        return "attack"
    return "normal"


def _incident_priority(grp: pd.DataFrame) -> str:
    if grp.empty:
        return "LOW"
    labels = grp["priority"].fillna("LOW").astype(str).str.upper().tolist()
    category_priority = CATEGORY_PRIORITY.get(str(grp["group_category"].iloc[0]).lower(), "LOW")
    labels.append(category_priority)
    return max(labels, key=lambda item: SEVERITY_RANK.get(item, 1))


def _required_columns() -> set[str]:
    return {
        "timestamp",
        "device_id",
        "device_type",
        "ward",
        "attack_type",
        "is_attack",
        "priority",
        "predicted_attack",
        "attack_label",
        "decision_action",
        "device_state",
        "src_ips",
        "life_support_involved",
        "created_at",
    }


def _cluster_prediction_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(group_category=[], group_id=[])

    df = df.copy()
    df["priority"] = _normalize_series(df["priority"]).str.upper().replace("", "LOW")
    df["attack_type"] = _normalize_series(df["attack_type"]).replace("", "normal")
    df["device_id"] = _normalize_series(df["device_id"]).replace("", "unknown")
    df["ward"] = _normalize_series(df["ward"]).replace("", "unknown")
    df["src_ips"] = _normalize_series(df.get("src_ips", pd.Series(dtype=str)))
    df["group_category"] = df.apply(_priority_label, axis=1)
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce").fillna(0).astype("int64")
    df = df.sort_values(["group_category", "device_id", "ward", "timestamp"]).reset_index(drop=True)

    group_ids = [-1] * len(df)
    next_group_id = 0

    for _, base_grp in df.groupby(["group_category", "device_id", "ward"], sort=False):
        base_grp = base_grp.sort_values("timestamp")
        current_indexes: list[int] = []
        last_timestamp: int | None = None
        for idx, row in base_grp.iterrows():
            timestamp = int(row["timestamp"])
            if current_indexes and last_timestamp is not None and timestamp - last_timestamp > WINDOW_MS:
                for current_idx in current_indexes:
                    group_ids[current_idx] = next_group_id
                next_group_id += 1
                current_indexes = []
            current_indexes.append(idx)
            last_timestamp = timestamp
        if current_indexes:
            for current_idx in current_indexes:
                group_ids[current_idx] = next_group_id
            next_group_id += 1

    df["group_id"] = group_ids
    return df


def _summarize_group(grp: pd.DataFrame) -> Dict[str, Any]:
    priorities = grp["priority"].fillna("LOW").astype(str).str.upper()
    incident_priority = _incident_priority(grp)
    return {
        "incident_id": f"INC-{int(grp['group_id'].iloc[0]):04d}",
        "group_id": int(grp["group_id"].iloc[0]),
        "group_category": str(grp["group_category"].mode().iat[0] if not grp["group_category"].mode().empty else grp["group_category"].iloc[0]),
        "alert_count": int(len(grp)),
        "attack_types": _split_joined_values(grp["attack_type"].tolist()),
        "wards_affected": _split_joined_values(grp["ward"].tolist()),
        "devices_affected": _split_joined_values(grp["device_id"].tolist()),
        "src_ips": _split_joined_values(grp["src_ips"].tolist()),
        "max_priority": incident_priority,
        "incident_priority": incident_priority,
        "life_support_involved": bool(grp["life_support_involved"].apply(_as_bool).any()),
        "predicted_attack_count": int(grp["predicted_attack"].apply(_as_bool).sum()),
        "normal_count": int((~grp["predicted_attack"].apply(_as_bool)).sum()),
        "critical_count": int((priorities == "CRITICAL").sum()),
        "high_count": int((priorities == "HIGH").sum()),
        "start_timestamp": int(grp["timestamp"].min()),
        "end_timestamp": int(grp["timestamp"].max()),
    }


def _save_charts(grouped: pd.DataFrame, incident_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    group_sizes = grouped["group_id"].value_counts().values if not grouped.empty else []
    if len(group_sizes):
        ax.hist(group_sizes, bins=min(10, max(1, len(group_sizes))), color="#1f77b4", edgecolor="black")
    ax.set_title("Prediction Group Size Distribution\n(Alert Grouping - Prediction Driven)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Prediction records per group")
    ax.set_ylabel("Number of groups")
    plt.tight_layout()
    plt.savefig(os.path.join(RES_DIR, "06_group_size_distribution.png"), dpi=150)
    plt.close()

    fig, ax = plt.subplots(figsize=(7, 4))
    category_counts = grouped["group_category"].value_counts().reindex(["critical", "high", "attack", "normal"], fill_value=0) if not grouped.empty else pd.Series([0, 0, 0, 0], index=["critical", "high", "attack", "normal"])
    category_counts.plot(kind="bar", ax=ax, color=["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"], edgecolor="black")
    ax.set_title("Incident Groups by Prediction Category", fontsize=11, fontweight="bold")
    ax.set_xlabel("Category")
    ax.set_ylabel("Group count")
    ax.tick_params(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(RES_DIR, "07_incidents_by_category.png"), dpi=150)
    plt.close()

    if not incident_df.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        pri_counts = incident_df["incident_priority"].value_counts().reindex(SEVERITY_ORDER, fill_value=0)
        pri_counts.plot(kind="bar", ax=ax, color=["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"], edgecolor="black")
        ax.set_title("Incident Priority After Prediction Grouping", fontsize=11, fontweight="bold")
        ax.set_xlabel("Priority")
        ax.set_ylabel("Incidents")
        ax.tick_params(rotation=0)
        plt.tight_layout()
        plt.savefig(os.path.join(RES_DIR, "08_incident_priority.png"), dpi=150)
        plt.close()


def main() -> None:
    print("=" * 65)
    print("  SCRIPT 04 - PREDICTION ALERT GROUPING")
    print("=" * 65)

    df = pd.read_csv(RAW_PATH)
    print(f"\n  Loaded prediction dataset: {len(df)} rows")

    missing = sorted(_required_columns() - set(df.columns))
    if missing:
        raise SystemExit(f"Prediction grouping input is missing required columns: {', '.join(missing)}")

    grouped_input = _cluster_prediction_rows(df)
    grouped = grouped_input[grouped_input["group_id"] >= 0].copy()
    total_records = len(grouped_input)
    n_groups = grouped["group_id"].nunique() if not grouped.empty else 0

    incident_rows: list[Dict[str, Any]] = []
    for _, grp in grouped.groupby("group_id", sort=True):
        incident_rows.append(_summarize_group(grp))

    incident_df = pd.DataFrame(incident_rows)

    print("\n  Grouping Results:")
    print(f"    Total prediction records : {total_records}")
    print(f"    Incident groups formed   : {n_groups}")
    print(f"    Category buckets         : {', '.join(sorted(set(grouped['group_category'])) if not grouped.empty else [])}")

    reduction = 0.0 if total_records == 0 else (1 - (n_groups / total_records)) * 100
    print(f"    Grouping reduction       : {reduction:.1f}%")

    if not incident_df.empty:
        print("\n  Sample Incident Groups:")
        print(
            incident_df[
                ["incident_id", "group_category", "alert_count", "attack_types", "wards_affected", "incident_priority"]
            ]
            .head(10)
            .to_string(index=False)
        )

    _save_charts(grouped, incident_df)

    grouped_output = grouped_input.copy()
    grouped_output.to_csv(os.path.join(PROC_DIR, "grouped_alerts.csv"), index=False)
    incident_df.to_csv(os.path.join(PROC_DIR, "grouped_incidents.csv"), index=False)

    with open(os.path.join(RES_DIR, "04_alert_grouping_summary.txt"), "w", encoding="utf-8") as handle:
        handle.write("IoMT Prediction Alert Grouping Summary - Novelty 2\n")
        handle.write("Student: MMM Ukasha  IT22904232\n")
        handle.write("=" * 60 + "\n\n")
        handle.write(f"Total prediction records : {total_records}\n")
        handle.write(f"Incident groups formed   : {n_groups}\n")
        handle.write(f"Grouping reduction       : {reduction:.1f}%\n\n")
        handle.write("Incident Groups:\n")
        handle.write(incident_df.to_string(index=False) if not incident_df.empty else "No grouped incidents available.\n")

    print("\n  Saved → data/processed/grouped_alerts.csv")
    print("  Saved → data/processed/grouped_incidents.csv")
    print("  Saved → results/04_alert_grouping_summary.txt")
    print(f"\n  📊  {total_records} prediction records → {n_groups} grouped incidents")
    print(f"  📉  Grouping reduction: {reduction:.1f}%")
    print("\n  ✅  SCRIPT 04 COMPLETE — Prediction grouping is ready for the Alert Grouping page")
    print("=" * 65)


if __name__ == "__main__":
    main()
