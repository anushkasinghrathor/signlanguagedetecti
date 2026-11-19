"""
Dynamic Gesture Classifier Training Pipeline (PyTorch LSTM)
----------------------------------------------------------
Loads 30-frame sequence arrays (.npy) from data/dynamic/<gesture_name>/,
trains a PyTorch LSTM model, and saves weights to models/dynamic_lstm.pt.
"""

import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
import yaml
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

from src.models.lstm import SignLanguageLSTM


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class DynamicGestureDataset(Dataset):
    """Loads 30-frame .npy landmark sequences from disk."""

    def __init__(self, data_dir: str, gestures: List[str]):
        self.samples: List[Tuple[Path, int]] = []
        self.gestures = sorted(gestures)
        self.label_to_idx = {g: idx for idx, g in enumerate(self.gestures)}
        self.idx_to_label = {idx: g for g, idx in self.label_to_idx.items()}

        base_path = Path(data_dir)
        for gesture in self.gestures:
            gesture_dir = base_path / gesture
            if not gesture_dir.exists():
                continue
            for npy_file in gesture_dir.glob("seq_*.npy"):
                self.samples.append((npy_file, self.label_to_idx[gesture]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        file_path, label = self.samples[idx]
        seq = np.load(file_path).astype(np.float32)  # Shape: (30, 126)

        # Invariant checks
        if seq.shape != (30, 126):
            raise ValueError(f"Expected shape (30, 126), got {seq.shape} in {file_path}")

        return torch.tensor(seq, dtype=torch.float32), label


def train_dynamic_model(
    data_dir: str = "data/dynamic",
    model_output_path: str = "models/dynamic_lstm.pt",
    label_map_output_path: str = "models/dynamic_labels.json",
    epochs: int = 40,
    batch_size: int = 8,
    lr: float = 1e-3,
    val_split: float = 0.2,
) -> float:
    """
    Trains the PyTorch LSTM model on dynamic gesture sequences.
    """
    config = load_config()
    gestures = config["vocabulary"]["dynamic_gestures"]

    dataset = DynamicGestureDataset(data_dir=data_dir, gestures=gestures)
    if len(dataset) == 0:
        raise FileNotFoundError(
            f"No sequence files found in {data_dir}. "
            "Please collect data using 'python -m src.data.collector --mode dynamic' first."
        )

    print(f"\nLoaded {len(dataset)} total dynamic gesture sequences.")
    for g in gestures:
        count = sum(1 for _, l in dataset.samples if dataset.idx_to_label[l] == g)
        print(f"  - {g}: {count} sequences")

    # Train / Val Split
    val_size = int(len(dataset) * val_split)
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(
        dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # Model Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nTraining on device: {device}")

    model = SignLanguageLSTM(
        input_size=126,
        hidden_size=128,
        num_layers=2,
        num_classes=len(gestures),
        dropout=0.2,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_acc = 0.0
    best_weights = None

    print("\n" + "=" * 50)
    print(" TRAINING LSTM DYNAMIC CLASSIFIER")
    print("=" * 50)

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss, train_correct = 0.0, 0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * batch_x.size(0)
            train_correct += (outputs.argmax(dim=1) == batch_y).sum().item()

        train_loss /= len(train_ds)
        train_acc = train_correct / len(train_ds)

        # Validation
        model.eval()
        val_loss, val_correct = 0.0, 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item() * batch_x.size(0)
                val_correct += (outputs.argmax(dim=1) == batch_y).sum().item()

        val_acc = val_correct / len(val_ds) if len(val_ds) > 0 else 1.0

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_weights = model.state_dict().copy()

        if epoch % 5 == 0 or epoch == epochs:
            print(
                f"Epoch [{epoch:02d}/{epochs:02d}] "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc * 100:.1f}% | "
                f"Val Acc: {val_acc * 100:.1f}%"
            )

    # Save best checkpoint
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": best_weights if best_weights else model.state_dict(),
            "input_size": 126,
            "hidden_size": 128,
            "num_layers": 2,
            "num_classes": len(gestures),
            "gestures": gestures,
        },
        model_output_path,
    )
    print(f"\n[+] Saved best LSTM weights: {model_output_path} (Val Acc: {best_val_acc * 100:.1f}%)")

    with open(label_map_output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "label_to_idx": dataset.label_to_idx,
                "idx_to_label": dataset.idx_to_label,
            },
            f,
            indent=2,
        )
    print(f"[+] Saved label mapping: {label_map_output_path}")

    return best_val_acc


if __name__ == "__main__":
    config = load_config()
    train_dynamic_model(
        data_dir=config["dataset"]["dynamic_dir"],
        model_output_path=config["models"]["dynamic_model_path"],
    )
