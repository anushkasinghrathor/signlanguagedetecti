"""
Pipeline & Model Inference Latency Benchmark
--------------------------------------------
Measures real execution latency inside `signenv` for:
  1. Static MLP single-frame inference (target: < 15.0 ms)
  2. Dynamic PyTorch LSTM 30-frame sequence inference (target: < 15.0 ms)
  3. Landmark normalization & temporal smoothing overhead
  4. MediaPipe HandDetector frame processing (target: >= 30 FPS / <= 33.3 ms)

Uses trained checkpoints in `models/` when present, or equivalent-architecture
models so the latency budget can be verified before and after dataset recording.

Usage:
    conda run -n signenv python scripts/benchmark_latency.py
"""

from pathlib import Path
import sys
import time
from typing import List, Tuple

import joblib
import numpy as np
from sklearn.neural_network import MLPClassifier
import torch

# Ensure project root is importable when invoked as `python scripts/benchmark_latency.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.lstm import SignLanguageLSTM
from src.pipeline.detector import HandDetector, normalize_landmarks
from src.pipeline.smoother import PredictionSmoother


def _stats(timings_ms: List[float]) -> Tuple[float, float]:
    arr = np.array(timings_ms, dtype=np.float64)
    return float(arr.mean()), float(np.percentile(arr, 95))


def benchmark_static_mlp(runs: int = 200) -> Tuple[float, float, str]:
    model_path = PROJECT_ROOT / "models" / "static_mlp.joblib"
    if model_path.exists():
        model = joblib.load(model_path)
        source = "trained checkpoint"
    else:
        # Match exact architecture from src/models/train_static.py: (128, 64)
        X = np.random.randn(40, 126).astype(np.float32)
        y = np.array([i % 5 for i in range(40)])
        model = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=10, random_state=42)
        model.fit(X, y)
        source = "equivalent architecture (untrained)"

    sample = np.random.randn(1, 126).astype(np.float32)
    # Warm-up
    for _ in range(10):
        model.predict_proba(sample)

    timings: List[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        model.predict_proba(sample)
        timings.append((time.perf_counter() - t0) * 1000.0)

    mean_ms, p95_ms = _stats(timings)
    return mean_ms, p95_ms, source


def benchmark_dynamic_lstm(runs: int = 100) -> Tuple[float, float, str]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = PROJECT_ROOT / "models" / "dynamic_lstm.pt"

    if model_path.exists():
        ckpt = torch.load(model_path, map_location=device, weights_only=True)
        model = SignLanguageLSTM(
            input_size=ckpt["input_size"],
            hidden_size=ckpt["hidden_size"],
            num_layers=ckpt["num_layers"],
            num_classes=ckpt["num_classes"],
        ).to(device)
        model.load_state_dict(ckpt["model_state_dict"])
        source = f"trained checkpoint ({device})"
    else:
        model = SignLanguageLSTM(
            input_size=126, hidden_size=128, num_layers=2, num_classes=3
        ).to(device)
        source = f"equivalent architecture ({device})"

    model.eval()
    seq = torch.randn(1, 30, 126, dtype=torch.float32, device=device)

    # Warm-up
    with torch.no_grad():
        for _ in range(10):
            model(seq)

    timings: List[float] = []
    with torch.no_grad():
        for _ in range(runs):
            t0 = time.perf_counter()
            logits = model(seq)
            _ = torch.softmax(logits, dim=1)
            timings.append((time.perf_counter() - t0) * 1000.0)

    mean_ms, p95_ms = _stats(timings)
    return mean_ms, p95_ms, source


def benchmark_normalization_and_smoother(runs: int = 500) -> Tuple[float, float]:
    pts = np.random.rand(21, 3).astype(np.float32)
    pts[9] = pts[0] + np.array([0.2, 0.3, 0.1], dtype=np.float32)
    smoother = PredictionSmoother(window_size=10, min_consensus=6, confidence_threshold=0.85)

    t_norm: List[float] = []
    t_smooth: List[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        normalize_landmarks(pts)
        t_norm.append((time.perf_counter() - t0) * 1000.0)

        t1 = time.perf_counter()
        smoother.update("Hello", 0.94, hands_detected=1)
        t_smooth.append((time.perf_counter() - t1) * 1000.0)

    return _stats(t_norm)[0], _stats(t_smooth)[0]


def benchmark_detector(runs: int = 40) -> Tuple[float, float]:
    detector = HandDetector(static_image_mode=False)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    try:
        # Warm-up MediaPipe TFLite graph
        for _ in range(5):
            detector.process_frame(frame, draw=False)

        timings: List[float] = []
        for _ in range(runs):
            t0 = time.perf_counter()
            detector.process_frame(frame, draw=False)
            timings.append((time.perf_counter() - t0) * 1000.0)
        return _stats(timings)
    finally:
        detector.close()


def main() -> None:
    print("=" * 68)
    print(" SIGN LANGUAGE RECOGNITION — LATENCY BUDGET BENCHMARK (signenv)")
    print("=" * 68)

    mlp_mean, mlp_p95, mlp_src = benchmark_static_mlp()
    lstm_mean, lstm_p95, lstm_src = benchmark_dynamic_lstm()
    norm_mean, smooth_mean = benchmark_normalization_and_smoother()
    det_mean, det_p95 = benchmark_detector()

    mlp_status = "PASS" if mlp_mean < 15.0 else "FAIL"
    lstm_status = "PASS" if lstm_mean < 15.0 else "FAIL"
    static_total = det_mean + mlp_mean + smooth_mean
    dynamic_total = det_mean + lstm_mean + smooth_mean

    print(f"Static MLP   ({mlp_src}):")
    print(f"  mean = {mlp_mean:.3f} ms | p95 = {mlp_p95:.3f} ms  [Target < 15.0 ms -> {mlp_status}]")
    print(f"Dynamic LSTM ({lstm_src}):")
    print(f"  mean = {lstm_mean:.3f} ms | p95 = {lstm_p95:.3f} ms  [Target < 15.0 ms -> {lstm_status}]")
    print(f"Landmark Normalization : mean = {norm_mean:.4f} ms")
    print(f"Prediction Smoother    : mean = {smooth_mean:.4f} ms")
    print(f"MediaPipe HandDetector : mean = {det_mean:.2f} ms | p95 = {det_p95:.2f} ms")
    print("-" * 68)
    print(
        f"Estimated Static Pipeline  : {static_total:.2f} ms/frame "
        f"(~{1000.0 / static_total:.1f} FPS)"
    )
    print(
        f"Estimated Dynamic Pipeline : {dynamic_total:.2f} ms/frame "
        f"(~{1000.0 / dynamic_total:.1f} FPS)"
    )
    print("=" * 68)

    if mlp_status != "PASS" or lstm_status != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
