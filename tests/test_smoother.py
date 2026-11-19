"""
Unit Tests for PredictionSmoother, Dataset Inspector, and App Inference Engine
------------------------------------------------------------------------------
Verifies temporal smoothing, flicker rejection, idle reset, data hygiene checks,
and hybrid AUTO routing between Static MLP and Dynamic PyTorch LSTM.
"""

from collections import deque
import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import torch

from src.app import SignInferenceEngine, render_hud
from src.data.inspect_data import inspect_dynamic_dataset, inspect_static_dataset
from src.models.lstm import SignLanguageLSTM
from src.models.train_static import train_static_model
from src.pipeline.smoother import PredictionSmoother, SmoothedPrediction


def test_smoother_rejects_low_confidence():
    """Predictions below confidence_threshold must never trigger a recognized sign."""
    smoother = PredictionSmoother(window_size=5, min_consensus=3, confidence_threshold=0.85)

    for _ in range(10):
        res = smoother.update("Hello", confidence=0.72, hands_detected=1)
        assert res.label == "Idle"
        assert res.is_new_trigger is False


def test_smoother_eliminates_flicker_and_locks_on_consensus():
    """Single-frame noise is ignored; sign locks in once min_consensus is reached."""
    smoother = PredictionSmoother(window_size=6, min_consensus=4, confidence_threshold=0.85)

    # Flickering mixed guesses should not trigger
    assert smoother.update("A", 0.95).label == "Idle"
    assert smoother.update("B", 0.95).label == "Idle"
    assert smoother.update("A", 0.95).label == "Idle"
    assert smoother.update("C", 0.95).label == "Idle"

    # Now sustain 'A' until 4 of the last 6 frames agree
    r1 = smoother.update("A", 0.92)
    assert r1.label == "Idle"
    r2 = smoother.update("A", 0.94)
    assert r2.label == "A"
    assert r2.is_new_trigger is True
    assert r2.confidence >= 0.90

    # Holding 'A' stays steady without re-triggering TTS
    r3 = smoother.update("A", 0.96)
    assert r3.label == "A"
    assert r3.is_new_trigger is False


def test_smoother_resets_after_hands_leave_frame():
    """Brief 1-frame tracking drop holds state; 3 empty frames reset cleanly to Idle."""
    smoother = PredictionSmoother(
        window_size=4, min_consensus=3, confidence_threshold=0.85, idle_reset_frames=3
    )

    for _ in range(3):
        smoother.update("Peace", 0.95, hands_detected=1)

    # 1-frame tracking blip should not immediately wipe label
    blip = smoother.update(None, 0.0, hands_detected=0)
    assert blip.label == "Peace"

    # 2 more empty frames complete the reset streak
    smoother.update(None, 0.0, hands_detected=0)
    reset_res = smoother.update(None, 0.0, hands_detected=0)
    assert reset_res.label == "Idle"


def test_dataset_inspector_valid_and_corrupted():
    """Verify inspect_data detects clean datasets and flags NaN/shape corruption."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # 1. Valid static CSV
        static_csv = tmp / "static_dataset.csv"
        rows = []
        for label in ["A", "B"]:
            for _ in range(5):
                row = {"label": label}
                for i in range(126):
                    row[f"f_{i}"] = 0.1
                rows.append(row)
        pd.DataFrame(rows).to_csv(static_csv, index=False)

        ok_static = inspect_static_dataset(str(static_csv))
        assert ok_static["issues"] == []
        assert ok_static["total_rows"] == 10

        # Inject a NaN value
        bad_df = pd.read_csv(static_csv)
        bad_df.loc[0, "f_5"] = np.nan
        bad_df.to_csv(static_csv, index=False)
        bad_static = inspect_static_dataset(str(static_csv))
        assert bad_static["nan_count"] == 1
        assert len(bad_static["issues"]) >= 1

        # 2. Dynamic sequences (1 valid class + 1 bad shape)
        dyn_dir = tmp / "dynamic"
        (dyn_dir / "Hello").mkdir(parents=True)
        (dyn_dir / "Yes").mkdir(parents=True)
        np.save(dyn_dir / "Hello" / "seq_000.npy", np.zeros((30, 126), dtype=np.float32))
        np.save(dyn_dir / "Yes" / "seq_000.npy", np.zeros((15, 126), dtype=np.float32))

        dyn_report = inspect_dynamic_dataset(str(dyn_dir), expected_seq_len=30)
        assert len(dyn_report["bad_shape_files"]) == 1


def test_inference_engine_fallback_and_auto_routing():
    """Verify engine handles missing models gracefully and routes AUTO by velocity."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # Missing models -> safe no-crash fallback
        empty_engine = SignInferenceEngine(
            static_model_path=str(tmp / "missing.joblib"),
            static_labels_path=str(tmp / "missing_s.json"),
            dynamic_model_path=str(tmp / "missing.pt"),
            dynamic_labels_path=str(tmp / "missing_d.json"),
        )
        assert empty_engine.has_static is False
        assert empty_engine.has_dynamic is False
        lbl, conf, branch = empty_engine.route_and_predict(
            mode="AUTO",
            feature_vector=np.zeros(126, dtype=np.float32),
            sequence_buffer=deque(maxlen=30),
            smoothed_velocity=0.01,
            velocity_threshold=0.04,
        )
        assert lbl is None and conf == 0.0 and branch == "NO_MODEL"

        # Now create real static + dynamic artifacts in temp dir
        csv_path = tmp / "static.csv"
        rows = []
        for cls_idx, label in enumerate(["A", "B"]):
            for _ in range(25):
                row = {"label": label}
                for i in range(126):
                    row[f"f_{i}"] = float(cls_idx) + 0.01 * np.random.randn()
                rows.append(row)
        pd.DataFrame(rows).to_csv(csv_path, index=False)

        static_model_path = tmp / "static_mlp.joblib"
        static_labels_path = tmp / "static_labels.json"
        train_static_model(str(csv_path), str(static_model_path), str(static_labels_path))

        dyn_model_path = tmp / "dynamic_lstm.pt"
        dyn_labels_path = tmp / "dynamic_labels.json"
        lstm = SignLanguageLSTM(input_size=126, hidden_size=32, num_layers=1, num_classes=2)
        torch.save(
            {
                "model_state_dict": lstm.state_dict(),
                "input_size": 126,
                "hidden_size": 32,
                "num_layers": 1,
                "num_classes": 2,
                "gestures": ["Hello", "Yes"],
            },
            dyn_model_path,
        )
        with open(dyn_labels_path, "w", encoding="utf-8") as f:
            json.dump({"idx_to_label": {"0": "Hello", "1": "Yes"}}, f)

        engine = SignInferenceEngine(
            static_model_path=str(static_model_path),
            static_labels_path=str(static_labels_path),
            dynamic_model_path=str(dyn_model_path),
            dynamic_labels_path=str(dyn_labels_path),
            sequence_length=30,
        )
        assert engine.has_static is True
        assert engine.has_dynamic is True

        seq_buf = deque([np.zeros(126, dtype=np.float32) for _ in range(30)], maxlen=30)

        # Low velocity -> AUTO routes to STATIC
        s_lbl, s_conf, s_branch = engine.route_and_predict(
            mode="AUTO",
            feature_vector=np.zeros(126, dtype=np.float32),
            sequence_buffer=seq_buf,
            smoothed_velocity=0.01,
            velocity_threshold=0.04,
        )
        assert s_branch == "STATIC"
        assert s_lbl in ("A", "B")
        assert 0.0 <= s_conf <= 1.0

        # High velocity + full 30-frame buffer -> AUTO routes to DYNAMIC
        d_lbl, d_conf, d_branch = engine.route_and_predict(
            mode="AUTO",
            feature_vector=np.zeros(126, dtype=np.float32),
            sequence_buffer=seq_buf,
            smoothed_velocity=0.08,
            velocity_threshold=0.04,
        )
        assert d_branch == "DYNAMIC"
        assert d_lbl in ("Hello", "Yes")
        assert 0.0 <= d_conf <= 1.0

        # Verify HUD renders cleanly without exceptions
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        hud = render_hud(
            frame=blank,
            prediction=SmoothedPrediction("Hello", 0.92, True),
            mode="AUTO",
            active_branch="DYNAMIC",
            fps=30.0,
            hands_count=1,
            tts_enabled=True,
            transcript=deque(["A", "Hello"], maxlen=5),
            models_loaded=(True, True),
        )
        assert hud.shape == (480, 640, 3)
