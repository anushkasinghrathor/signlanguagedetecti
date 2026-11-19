"""
Interactive Sign Language Dataset Collector
-------------------------------------------
Captures both static (single-frame) and dynamic (30-frame sequence) sign language
datasets from webcam using normalized 126-D MediaPipe hand landmarks.

Usage:
    conda run -n signenv python -m src.data.collector --mode static
    conda run -n signenv python -m src.data.collector --mode dynamic
"""

import os
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np
import yaml

from src.pipeline.detector import HandDetector


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    """Load project configuration safely from YAML file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def draw_hud(
    frame: np.ndarray,
    gesture_name: str,
    collected_count: int,
    target_count: int,
    state: str,
    countdown_val: int = 0,
    hands_detected: int = 0,
) -> np.ndarray:
    """Renders visual cards, progress metrics, and instructions onto the frame."""
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # Draw semi-transparent header bar
    cv2.rectangle(overlay, (0, 0), (w, 85), (20, 20, 20), -1)
    # Draw bottom control bar
    cv2.rectangle(overlay, (0, h - 50), (w, h), (20, 20, 20), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    # Header text
    cv2.putText(
        frame,
        f"TARGET SIGN: {gesture_name.upper()}",
        (20, 35),
        cv2.FONT_HERSHEY_DUPLEX,
        0.8,
        (0, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        f"Progress: {collected_count}/{target_count}",
        (20, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )

    # Hands detected indicator
    color_hands = (0, 255, 0) if hands_detected > 0 else (0, 0, 255)
    cv2.putText(
        frame,
        f"Hands: {hands_detected}",
        (w - 140, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color_hands,
        2,
    )

    # State / Action banner
    if state == "COUNTDOWN":
        # Draw large countdown in center
        cv2.circle(frame, (w // 2, h // 2), 65, (0, 165, 255), -1)
        cv2.putText(
            frame,
            str(countdown_val),
            (w // 2 - 20, h // 2 + 25),
            cv2.FONT_HERSHEY_DUPLEX,
            2.2,
            (255, 255, 255),
            4,
        )
    elif state == "RECORDING":
        cv2.circle(frame, (w - 30, 65), 10, (0, 0, 255), -1)
        cv2.putText(
            frame,
            "REC",
            (w - 90, 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
    elif state == "READY":
        cv2.putText(
            frame,
            "READY - Press SPACE to start",
            (w // 2 - 180, h // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

    # Bottom helper bar
    cv2.putText(
        frame,
        "[SPACE] Start/Resume | [N] Next Sign | [Q] Quit & Save",
        (20, h - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
    )
    return frame


def collect_static_gestures(config: Dict[str, Any]):
    """
    Collects single-frame normalized landmark vectors (shape: [126,])
    and writes them into a unified CSV file: data/static/static_dataset.csv
    """
    output_dir = Path(config["dataset"]["static_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_file = output_dir / "static_dataset.csv"

    gestures = config["vocabulary"]["static_gestures"]
    target_samples = config["dataset"]["samples_per_static_class"]

    # Initialize CSV with header if it doesn't exist
    if not dataset_file.exists():
        header = ["label"] + [f"f_{i}" for i in range(126)]
        with open(dataset_file, "w", encoding="utf-8") as f:
            f.write(",".join(header) + "\n")

    detector = HandDetector(
        min_detection_confidence=config["mediapipe"]["min_detection_confidence"],
        min_tracking_confidence=config["mediapipe"]["min_tracking_confidence"],
    )

    cap = cv2.VideoCapture(config["camera"]["index"])
    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam index {config['camera']['index']}.")

    print("\n" + "=" * 60)
    print(" STATIC GESTURE COLLECTOR")
    print(f" Vocabulary: {gestures}")
    print(f" Target samples per sign: {target_samples}")
    print("=" * 60)

    try:
        for gesture in gestures:
            collected = 0
            state = "READY"
            countdown_val = 3
            countdown_start = 0.0

            while collected < target_samples:
                ret, frame = cap.read()
                if not ret:
                    break

                # Frame pre-processing and landmark extraction
                annotated, features, hands_count, _ = detector.process_frame(frame, draw=True)

                # State machine
                now = time.time()
                if state == "COUNTDOWN":
                    elapsed = now - countdown_start
                    countdown_val = max(1, 3 - int(elapsed))
                    if elapsed >= 3.0:
                        state = "RECORDING"
                elif state == "RECORDING":
                    # Only save if at least one hand is detected in frame
                    if hands_count > 0:
                        row = [gesture] + [f"{val:.6f}" for val in features]
                        with open(dataset_file, "a", encoding="utf-8") as f:
                            f.write(",".join(row) + "\n")
                        collected += 1
                        time.sleep(0.03)  # Small pacing interval (~30 FPS capture)

                display_frame = draw_hud(
                    annotated,
                    gesture,
                    collected,
                    target_samples,
                    state,
                    countdown_val,
                    hands_count,
                )
                cv2.imshow("Sign Language Data Collector (Static)", display_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print(f"\nUser exited. Collected data saved to {dataset_file}")
                    return
                elif key == ord(" "):
                    if state == "READY":
                        state = "COUNTDOWN"
                        countdown_start = time.time()
                elif key == ord("n"):
                    print(f"\nSkipped {gesture}. Moving to next...")
                    break

            print(f" Completed '{gesture}' ({collected}/{target_samples} samples).")

        print(f"\nAll static gestures completed! Dataset saved to: {dataset_file}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()


def collect_dynamic_gestures(config: Dict[str, Any]):
    """
    Collects 30-frame temporal sequences (shape: [30, 126])
    and writes them into data/dynamic/<gesture_name>/sequence_X.npy
    """
    base_dir = Path(config["dataset"]["dynamic_dir"])
    base_dir.mkdir(parents=True, exist_ok=True)

    gestures = config["vocabulary"]["dynamic_gestures"]
    target_sequences = config["dataset"]["sequences_per_dynamic_class"]
    seq_length = config["dataset"]["sequence_length"]  # 30 frames

    detector = HandDetector(
        min_detection_confidence=config["mediapipe"]["min_detection_confidence"],
        min_tracking_confidence=config["mediapipe"]["min_tracking_confidence"],
    )

    cap = cv2.VideoCapture(config["camera"]["index"])
    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam index {config['camera']['index']}.")

    print("\n" + "=" * 60)
    print(" DYNAMIC GESTURE COLLECTOR")
    print(f" Vocabulary: {gestures}")
    print(f" Target sequences per sign: {target_sequences} (30 frames each)")
    print("=" * 60)

    try:
        for gesture in gestures:
            gesture_dir = base_dir / gesture
            gesture_dir.mkdir(parents=True, exist_ok=True)

            # Determine next sequence index based on existing files
            existing_files = list(gesture_dir.glob("seq_*.npy"))
            seq_idx = len(existing_files)

            while seq_idx < target_sequences:
                # Wait for user trigger with countdown
                state = "READY"
                countdown_start = 0.0
                countdown_val = 3

                while state != "RECORDING":
                    ret, frame = cap.read()
                    if not ret:
                        break
                    annotated, _, hands_count, _ = detector.process_frame(frame, draw=True)

                    if state == "COUNTDOWN":
                        elapsed = time.time() - countdown_start
                        countdown_val = max(1, 3 - int(elapsed))
                        if elapsed >= 3.0:
                            state = "RECORDING"

                    display_frame = draw_hud(
                        annotated,
                        gesture,
                        seq_idx,
                        target_sequences,
                        state,
                        countdown_val,
                        hands_count,
                    )
                    cv2.imshow("Sign Language Data Collector (Dynamic)", display_frame)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        print("\nUser exited.")
                        return
                    elif key == ord(" "):
                        if state == "READY":
                            state = "COUNTDOWN"
                            countdown_start = time.time()
                    elif key == ord("n"):
                        break

                if key == ord("n"):
                    break

                # Record 30 consecutive frames
                sequence_frames: List[np.ndarray] = []
                for frame_idx in range(seq_length):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    annotated, features, hands_count, _ = detector.process_frame(frame, draw=True)
                    sequence_frames.append(features)

                    # Visual feedback while recording sequence
                    cv2.putText(
                        annotated,
                        f"RECORDING MOTION: {frame_idx + 1}/{seq_length}",
                        (20, 120),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )
                    display = draw_hud(
                        annotated,
                        gesture,
                        seq_idx,
                        target_sequences,
                        "RECORDING",
                        0,
                        hands_count,
                    )
                    cv2.imshow("Sign Language Data Collector (Dynamic)", display)
                    cv2.waitKey(1)

                if len(sequence_frames) == seq_length:
                    seq_array = np.array(sequence_frames, dtype=np.float32)  # Shape: (30, 126)
                    save_path = gesture_dir / f"seq_{seq_idx:03d}.npy"
                    np.save(save_path, seq_array)
                    seq_idx += 1
                    print(f"  [+] Saved {gesture} sequence #{seq_idx:03d}")

            print(f" Completed '{gesture}' dynamic sequences.")

        print(f"\nAll dynamic gestures recorded! Saved under: {base_dir}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()


def main():
    parser = argparse.ArgumentParser(description="Sign Language Dataset Collector")
    parser.add_argument(
        "--mode",
        choices=["static", "dynamic"],
        default="static",
        help="Type of gestures to collect ('static' for MLP, 'dynamic' for LSTM)",
    )
    parser.add_argument(
        "--config",
        default="configs/config.yaml",
        help="Path to project configuration YAML",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.mode == "static":
        collect_static_gestures(config)
    else:
        collect_dynamic_gestures(config)


if __name__ == "__main__":
    main()
