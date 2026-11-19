"""
Dataset Health & Validation Inspector
-------------------------------------
Checks collected static CSV and dynamic .npy datasets for missing files,
class imbalance, NaN/Inf values, and exact feature/sequence shapes before training.

Usage:
    conda run -n signenv python -m src.data.inspect_data
"""

from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import yaml


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def inspect_static_dataset(csv_path: str) -> Dict[str, Any]:
    """Validates static CSV dataset shape, class distribution, and numeric hygiene."""
    report: Dict[str, Any] = {
        "path": csv_path,
        "exists": False,
        "total_rows": 0,
        "feature_count": 0,
        "class_counts": {},
        "nan_count": 0,
        "inf_count": 0,
        "issues": [],
    }

    file_path = Path(csv_path)
    if not file_path.exists():
        report["issues"].append(f"Static dataset file not found at {csv_path}.")
        return report

    report["exists"] = True
    df = pd.read_csv(file_path)
    report["total_rows"] = len(df)

    if df.empty:
        report["issues"].append("Static dataset CSV is empty.")
        return report

    if "label" not in df.columns:
        report["issues"].append("Missing required 'label' column.")
        return report

    feature_cols = [c for c in df.columns if c.startswith("f_")]
    report["feature_count"] = len(feature_cols)
    if len(feature_cols) != 126:
        report["issues"].append(f"Expected 126 feature columns, found {len(feature_cols)}.")

    report["class_counts"] = df["label"].value_counts().to_dict()
    if len(report["class_counts"]) < 2:
        report["issues"].append("At least 2 distinct static classes are required for training.")

    values = df[feature_cols].to_numpy(dtype=np.float64, copy=False)
    nan_count = int(np.isnan(values).sum())
    inf_count = int(np.isinf(values).sum())
    report["nan_count"] = nan_count
    report["inf_count"] = inf_count

    if nan_count > 0:
        report["issues"].append(f"Found {nan_count} NaN values in static features.")
    if inf_count > 0:
        report["issues"].append(f"Found {inf_count} Inf values in static features.")

    return report


def inspect_dynamic_dataset(
    dynamic_dir: str,
    expected_seq_len: int = 30,
    expected_features: int = 126,
) -> Dict[str, Any]:
    """Validates dynamic .npy sequence folders for shape integrity and numeric hygiene."""
    report: Dict[str, Any] = {
        "path": dynamic_dir,
        "exists": False,
        "total_sequences": 0,
        "class_counts": {},
        "bad_shape_files": [],
        "nan_or_inf_files": [],
        "issues": [],
    }

    base_path = Path(dynamic_dir)
    if not base_path.exists():
        report["issues"].append(f"Dynamic dataset directory not found at {dynamic_dir}.")
        return report

    report["exists"] = True
    gesture_dirs = sorted([d for d in base_path.iterdir() if d.is_dir()])

    for gesture_dir in gesture_dirs:
        npy_files = sorted(gesture_dir.glob("seq_*.npy"))
        report["class_counts"][gesture_dir.name] = len(npy_files)
        report["total_sequences"] += len(npy_files)

        for npy_file in npy_files:
            arr = np.load(npy_file)
            if arr.shape != (expected_seq_len, expected_features):
                report["bad_shape_files"].append((str(npy_file), arr.shape))
            elif np.isnan(arr).any() or np.isinf(arr).any():
                report["nan_or_inf_files"].append(str(npy_file))

    if report["total_sequences"] == 0:
        report["issues"].append("No dynamic sequence (.npy) files found.")
    if len(report["class_counts"]) < 2:
        report["issues"].append("At least 2 distinct dynamic classes are required for training.")
    if report["bad_shape_files"]:
        report["issues"].append(
            f"{len(report['bad_shape_files'])} sequence files have unexpected shapes."
        )
    if report["nan_or_inf_files"]:
        report["issues"].append(
            f"{len(report['nan_or_inf_files'])} sequence files contain NaN or Inf values."
        )

    return report


def print_report(title: str, report: Dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)
    print(f"Path: {report['path']}")
    print(f"Exists: {report['exists']}")
    if "total_rows" in report:
        print(f"Total Samples: {report['total_rows']} | Features: {report['feature_count']}")
        print(f"NaN Count: {report['nan_count']} | Inf Count: {report['inf_count']}")
    else:
        print(f"Total Sequences: {report['total_sequences']}")
        print(f"Bad Shape Files: {len(report['bad_shape_files'])}")
        print(f"NaN/Inf Files: {len(report['nan_or_inf_files'])}")

    print("Class Distribution:")
    if report["class_counts"]:
        for cls_name, count in report["class_counts"].items():
            print(f"  - {cls_name}: {count}")
    else:
        print("  (none)")

    if report["issues"]:
        print("Issues Found:")
        for issue in report["issues"]:
            print(f"  [!] {issue}")
    else:
        print("Status: READY FOR TRAINING")


def main() -> None:
    config = load_config()
    static_csv = f"{config['dataset']['static_dir']}/static_dataset.csv"
    dynamic_dir = config["dataset"]["dynamic_dir"]
    seq_len = config["dataset"]["sequence_length"]

    static_report = inspect_static_dataset(static_csv)
    dynamic_report = inspect_dynamic_dataset(dynamic_dir, expected_seq_len=seq_len)

    print_report("STATIC DATASET REPORT", static_report)
    print_report("DYNAMIC DATASET REPORT", dynamic_report)


if __name__ == "__main__":
    main()
