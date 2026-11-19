"""
Static Gesture Classifier Training Pipeline (MLP)
------------------------------------------------
Trains a Multi-Layer Perceptron (MLP) on 126-D static hand landmark vectors.
Saves model artifacts to models/static_mlp.joblib and label mapping to models/static_labels.json.

# INVARIANT: Input feature dimension is strictly 126.
# INVARIANT: Stratified splitting ensures class balance across train and evaluation sets.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def train_static_model(
    data_path: str = "data/static/static_dataset.csv",
    model_output_path: str = "models/static_mlp.joblib",
    label_map_output_path: str = "models/static_labels.json",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[MLPClassifier, float]:
    """
    Trains an MLP classifier on the static gesture dataset.

    Returns:
        model: Trained scikit-learn MLPClassifier
        accuracy: Test set accuracy score
    """
    data_file = Path(data_path)
    if not data_file.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_file}. "
            "Please collect data using 'python -m src.data.collector --mode static' first."
        )

    df = pd.read_csv(data_file)
    if df.empty or "label" not in df.columns:
        raise ValueError("Dataset is empty or missing the 'label' column.")

    print(f"\nLoaded dataset with {len(df)} total samples.")
    print(f"Class distribution:\n{df['label'].value_counts()}\n")

    # Features (126 dimensions) and target label
    feature_cols = [c for c in df.columns if c.startswith("f_")]
    if len(feature_cols) != 126:
        raise ValueError(f"Expected 126 feature columns, found {len(feature_cols)}.")

    X = df[feature_cols].values.astype(np.float32)
    y_raw = df["label"].values

    # Build bidirectional label mapping
    unique_labels = sorted(list(set(y_raw)))
    label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
    idx_to_label = {idx: label for label, idx in label_to_idx.items()}
    y = np.array([label_to_idx[l] for l in y_raw], dtype=np.int64)

    # Stratified split to preserve class ratios
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    print(f"Train samples: {len(X_train)} | Test samples: {len(X_test)}")

    # MLP Architecture
    # WHY: Two hidden layers (128 -> 64) provide sufficient capacity to separate
    # 21-joint spatial angles without overfitting small datasets.
    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation="relu",
        solver="adam",
        max_iter=500,
        early_stopping=True,
        n_iter_no_change=20,
        random_state=random_state,
        verbose=False,
    )

    print("Training MLP static classifier...")
    mlp.fit(X_train, y_train)

    # Evaluation
    y_pred = mlp.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("\n" + "=" * 60)
    print(f" EVALUATION REPORT (Test Accuracy: {accuracy * 100:.2f}%)")
    print("=" * 60)
    target_names = [idx_to_label[i] for i in range(len(unique_labels))]
    print(classification_report(y_test, y_pred, target_names=target_names))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Save artifacts
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(mlp, model_output_path)
    print(f"\n[+] Saved trained model: {model_output_path}")

    with open(label_map_output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"label_to_idx": label_to_idx, "idx_to_label": idx_to_label},
            f,
            indent=2,
        )
    print(f"[+] Saved label mapping: {label_map_output_path}")

    return mlp, accuracy


if __name__ == "__main__":
    config = load_config()
    train_static_model(
        data_path=f"{config['dataset']['static_dir']}/static_dataset.csv",
        model_output_path=config["models"]["static_model_path"],
    )
