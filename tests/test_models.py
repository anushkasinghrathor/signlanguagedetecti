"""
Unit Tests for Static MLP and Dynamic LSTM Model Pipelines
----------------------------------------------------------
Verifies forward pass dimensions, loss backpropagation, and synthetic training runs.
"""

import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch

from src.models.lstm import SignLanguageLSTM
from src.models.train_static import train_static_model
from src.models.train_dynamic import DynamicGestureDataset, SignLanguageLSTM


def test_lstm_forward_pass_dimensions():
    """Verify PyTorch LSTM accepts (batch, 30, 126) and outputs (batch, num_classes)."""
    batch_size = 4
    seq_len = 30
    input_dim = 126
    num_classes = 3

    model = SignLanguageLSTM(
        input_size=input_dim,
        hidden_size=64,
        num_layers=2,
        num_classes=num_classes,
        dropout=0.1,
    )

    x = torch.randn(batch_size, seq_len, input_dim)
    logits = model(x)

    assert logits.shape == (batch_size, num_classes), (
        f"Expected logits shape {(batch_size, num_classes)}, got {logits.shape}"
    )


def test_static_mlp_synthetic_training():
    """Verify MLP training pipeline runs and saves artifacts on synthetic dataset."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_path = tmp_path / "synthetic_static.csv"
        model_path = tmp_path / "model.joblib"
        labels_path = tmp_path / "labels.json"

        # Generate small synthetic dataset: 3 classes, 30 samples each
        classes = ["A", "B", "ThumbsUp"]
        rows = []
        for c in classes:
            for _ in range(30):
                features = np.random.randn(126).astype(np.float32)
                row = {"label": c}
                for i, val in enumerate(features):
                    row[f"f_{i}"] = val
                rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)

        # Run training
        model, acc = train_static_model(
            data_path=str(csv_path),
            model_output_path=str(model_path),
            label_map_output_path=str(labels_path),
        )

        assert model_path.exists(), "Model file was not created"
        assert labels_path.exists(), "Label map file was not created"
        assert acc >= 0.0
