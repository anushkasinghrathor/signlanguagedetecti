"""
Real-Time Sign Language Recognition Desktop Application
-------------------------------------------------------
Standalone real-time desktop application integrating:
  Webcam -> MediaPipe 126-D Landmarks -> Hybrid Static MLP / Dynamic LSTM
         -> Temporal Smoothing -> On-Screen Text HUD + Non-Blocking TTS Audio

Usage:
    conda run -n signenv python -m src.app

Controls:
    [M] Cycle routing mode: AUTO -> STATIC -> DYNAMIC
    [S] Toggle Text-to-Speech audio ON / MUTED
    [C] Clear recent word transcript
    [Q] Quit safely and release hardware resources
"""

import argparse
from collections import deque
import json
from pathlib import Path
import time
from typing import Any, Deque, Dict, Optional, Tuple

import cv2
import joblib
import numpy as np
import torch
import yaml

from src.models.lstm import SignLanguageLSTM
from src.pipeline.detector import HandDetector
from src.pipeline.smoother import PredictionSmoother, SmoothedPrediction
from src.tts.speaker import TextToSpeechWorker


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class SignInferenceEngine:
    """
    Loads available trained models (Static MLP & Dynamic PyTorch LSTM) and routes
    incoming 126-D hand landmarks based on routing mode and hand motion velocity.
    """

    def __init__(
        self,
        static_model_path: str = "models/static_mlp.joblib",
        static_labels_path: str = "models/static_labels.json",
        dynamic_model_path: str = "models/dynamic_lstm.pt",
        dynamic_labels_path: str = "models/dynamic_labels.json",
        sequence_length: int = 30,
    ):
        self.sequence_length = sequence_length
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.static_model = None
        self.static_idx_to_label: Dict[int, str] = {}

        self.dynamic_model: Optional[SignLanguageLSTM] = None
        self.dynamic_idx_to_label: Dict[int, str] = {}

        self._load_static(static_model_path, static_labels_path)
        self._load_dynamic(dynamic_model_path, dynamic_labels_path)

    def _load_static(self, model_path: str, labels_path: str) -> None:
        m_path, l_path = Path(model_path), Path(labels_path)
        if not (m_path.exists() and l_path.exists()):
            return
        self.static_model = joblib.load(m_path)
        with open(l_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.static_idx_to_label = {int(k): v for k, v in data["idx_to_label"].items()}

    def _load_dynamic(self, model_path: str, labels_path: str) -> None:
        m_path, l_path = Path(model_path), Path(labels_path)
        if not (m_path.exists() and l_path.exists()):
            return
        checkpoint = torch.load(m_path, map_location=self.device, weights_only=True)
        model = SignLanguageLSTM(
            input_size=checkpoint["input_size"],
            hidden_size=checkpoint["hidden_size"],
            num_layers=checkpoint["num_layers"],
            num_classes=checkpoint["num_classes"],
        ).to(self.device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        self.dynamic_model = model

        with open(l_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.dynamic_idx_to_label = {int(k): v for k, v in data["idx_to_label"].items()}

    @property
    def has_static(self) -> bool:
        return self.static_model is not None

    @property
    def has_dynamic(self) -> bool:
        return self.dynamic_model is not None

    def predict_static(self, feature_vector: np.ndarray) -> Tuple[Optional[str], float]:
        if not self.has_static:
            return None, 0.0
        probs = self.static_model.predict_proba(feature_vector.reshape(1, -1))[0]
        best_idx = int(np.argmax(probs))
        return self.static_idx_to_label.get(best_idx), float(probs[best_idx])

    def predict_dynamic(self, sequence: np.ndarray) -> Tuple[Optional[str], float]:
        if not self.has_dynamic:
            return None, 0.0
        # INVARIANT: LSTM expects shape (batch=1, seq_len=30, features=126)
        tensor_x = torch.tensor(sequence, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            logits = self.dynamic_model(tensor_x)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
        best_idx = int(np.argmax(probs))
        return self.dynamic_idx_to_label.get(best_idx), float(probs[best_idx])

    def route_and_predict(
        self,
        mode: str,
        feature_vector: np.ndarray,
        sequence_buffer: Deque[np.ndarray],
        smoothed_velocity: float,
        velocity_threshold: float,
    ) -> Tuple[Optional[str], float, str]:
        """
        Routes the current frame/sequence to either the Static MLP or Dynamic LSTM.
        Returns: (predicted_label, confidence, active_branch_name)
        """
        buffer_ready = len(sequence_buffer) == self.sequence_length

        if mode == "STATIC":
            if self.has_static:
                lbl, conf = self.predict_static(feature_vector)
                return lbl, conf, "STATIC"
            return None, 0.0, "NO_STATIC_MODEL"

        if mode == "DYNAMIC":
            if self.has_dynamic and buffer_ready:
                seq = np.array(sequence_buffer, dtype=np.float32)
                lbl, conf = self.predict_dynamic(seq)
                return lbl, conf, "DYNAMIC"
            return None, 0.0, "BUFFERING" if self.has_dynamic else "NO_DYNAMIC_MODEL"

        # AUTO mode: select based on smoothed hand velocity
        if smoothed_velocity >= velocity_threshold and self.has_dynamic and buffer_ready:
            seq = np.array(sequence_buffer, dtype=np.float32)
            lbl, conf = self.predict_dynamic(seq)
            return lbl, conf, "DYNAMIC"

        if self.has_static:
            lbl, conf = self.predict_static(feature_vector)
            return lbl, conf, "STATIC"

        if self.has_dynamic and buffer_ready:
            seq = np.array(sequence_buffer, dtype=np.float32)
            lbl, conf = self.predict_dynamic(seq)
            return lbl, conf, "DYNAMIC"

        return None, 0.0, "NO_MODEL"


def render_hud(
    frame: np.ndarray,
    prediction: SmoothedPrediction,
    mode: str,
    active_branch: str,
    fps: float,
    hands_count: int,
    tts_enabled: bool,
    transcript: Deque[str],
    models_loaded: Tuple[bool, bool],
) -> np.ndarray:
    """Draws clean real-time HUD overlay with sign text, confidence bar, and system metrics."""
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # Top header bar & bottom prediction panel
    cv2.rectangle(overlay, (0, 0), (w, 52), (18, 18, 22), -1)
    cv2.rectangle(overlay, (0, h - 130), (w, h), (18, 18, 22), -1)
    frame = cv2.addWeighted(overlay, 0.78, frame, 0.22, 0)

    # Top metrics: Mode, FPS, Hands, Sound
    cv2.putText(
        frame,
        f"MODE: {mode} ({active_branch})",
        (14, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (0, 230, 255),
        2,
    )
    cv2.putText(
        frame,
        f"FPS: {fps:.0f}",
        (w - 285, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (230, 230, 230),
        2,
    )
    hand_color = (80, 255, 80) if hands_count > 0 else (90, 90, 255)
    cv2.putText(
        frame,
        f"Hands: {hands_count}",
        (w - 195, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        hand_color,
        2,
    )
    sound_txt = "AUDIO: ON" if tts_enabled else "AUDIO: OFF"
    sound_col = (80, 255, 80) if tts_enabled else (120, 120, 120)
    cv2.putText(
        frame,
        sound_txt,
        (w - 102, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        sound_col,
        2,
    )

    # Helpful notice if models are not yet trained
    has_static, has_dynamic = models_loaded
    if not has_static and not has_dynamic:
        cv2.rectangle(frame, (14, 62), (w - 14, 96), (0, 120, 220), -1)
        cv2.putText(
            frame,
            "No trained models found yet - tracking hands only (run collector & trainer)",
            (22, 84),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.47,
            (255, 255, 255),
            1,
        )

    # Main recognized sign text
    is_idle = prediction.label == PredictionSmoother.IDLE_LABEL
    sign_color = (160, 160, 160) if is_idle else (80, 255, 140)
    cv2.putText(
        frame,
        f"SIGN: {prediction.label}",
        (18, h - 88),
        cv2.FONT_HERSHEY_DUPLEX,
        0.95,
        sign_color,
        2,
    )

    # Confidence progress bar
    bar_x, bar_y, bar_w, bar_h = w - 210, h - 106, 190, 20
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (70, 70, 70), -1)
    fill_w = int(bar_w * max(0.0, min(1.0, prediction.confidence)))
    bar_color = (80, 230, 100) if prediction.confidence >= 0.85 else (0, 180, 255)
    if fill_w > 0:
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), bar_color, -1)
    cv2.putText(
        frame,
        f"{prediction.confidence * 100:.0f}%",
        (bar_x + bar_w - 46, bar_y + 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (255, 255, 255),
        1,
    )

    # Recent recognized words strip
    recent_text = " | ".join(transcript) if transcript else "(waiting for signs...)"
    cv2.putText(
        frame,
        f"History: {recent_text}",
        (18, h - 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (225, 225, 225),
        1,
    )

    # Footer controls
    cv2.putText(
        frame,
        "[M] Mode  |  [S] Sound ON/OFF  |  [C] Clear History  |  [Q] Quit",
        (18, h - 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (180, 180, 180),
        1,
    )
    return frame


def run_app(config_path: str = "configs/config.yaml") -> None:
    """Runs the standalone real-time sign language recognition desktop app."""
    config = load_config(config_path)

    seq_len = int(config["dataset"]["sequence_length"])
    conf_threshold = float(config["models"]["confidence_threshold"])
    vel_threshold = float(config["models"]["velocity_threshold"])

    engine = SignInferenceEngine(
        static_model_path=config["models"]["static_model_path"],
        static_labels_path="models/static_labels.json",
        dynamic_model_path=config["models"]["dynamic_model_path"],
        dynamic_labels_path="models/dynamic_labels.json",
        sequence_length=seq_len,
    )

    print("\n" + "=" * 60)
    print(" REAL-TIME SIGN LANGUAGE RECOGNITION")
    print(f" Static MLP Loaded : {engine.has_static}")
    print(f" Dynamic LSTM Loaded: {engine.has_dynamic}")
    print("=" * 60)

    detector = HandDetector(
        max_num_hands=int(config["mediapipe"]["max_num_hands"]),
        min_detection_confidence=float(config["mediapipe"]["min_detection_confidence"]),
        min_tracking_confidence=float(config["mediapipe"]["min_tracking_confidence"]),
    )
    smoother = PredictionSmoother(
        window_size=10,
        min_consensus=6,
        confidence_threshold=conf_threshold,
        idle_reset_frames=3,
    )
    tts = TextToSpeechWorker(
        rate=int(config["tts"]["rate"]),
        volume=float(config["tts"]["volume"]),
        cooldown_seconds=float(config["tts"]["cooldown_seconds"]),
        enabled=bool(config["tts"]["enabled"]),
    )

    cap = cv2.VideoCapture(int(config["camera"]["index"]))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(config["camera"]["width"]))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(config["camera"]["height"]))

    if not cap.isOpened():
        tts.stop()
        detector.close()
        raise RuntimeError(f"Could not open webcam index {config['camera']['index']}.")

    modes = ["AUTO", "STATIC", "DYNAMIC"]
    mode_idx = 0

    sequence_buffer: Deque[np.ndarray] = deque(maxlen=seq_len)
    velocity_window: Deque[float] = deque(maxlen=5)
    transcript: Deque[str] = deque(maxlen=5)

    prev_time = time.monotonic()
    fps = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Warning: Failed to read frame from webcam. Exiting.")
                break

            # Mirror view feels natural for live signers
            frame = cv2.flip(frame, 1)

            annotated, features, hands_count, velocity = detector.process_frame(frame, draw=True)

            if hands_count > 0:
                sequence_buffer.append(features)
                velocity_window.append(velocity)
                smoothed_vel = sum(velocity_window) / len(velocity_window)

                raw_label, raw_conf, active_branch = engine.route_and_predict(
                    mode=modes[mode_idx],
                    feature_vector=features,
                    sequence_buffer=sequence_buffer,
                    smoothed_velocity=smoothed_vel,
                    velocity_threshold=vel_threshold,
                )
            else:
                sequence_buffer.clear()
                velocity_window.clear()
                raw_label, raw_conf, active_branch = None, 0.0, "IDLE"

            prediction = smoother.update(raw_label, raw_conf, hands_detected=hands_count)

            # Trigger non-blocking speech & append transcript when a new sign locks in
            if prediction.is_new_trigger and prediction.label != PredictionSmoother.IDLE_LABEL:
                transcript.append(prediction.label)
                tts.speak(prediction.label)

            # Smooth FPS calculation
            now = time.monotonic()
            dt = now - prev_time
            prev_time = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps > 0 else (1.0 / dt)

            hud_frame = render_hud(
                frame=annotated,
                prediction=prediction,
                mode=modes[mode_idx],
                active_branch=active_branch,
                fps=fps,
                hands_count=hands_count,
                tts_enabled=tts.enabled,
                transcript=transcript,
                models_loaded=(engine.has_static, engine.has_dynamic),
            )
            cv2.imshow("Sign Language Recognition", hud_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("m"):
                mode_idx = (mode_idx + 1) % len(modes)
                smoother.reset()
            elif key == ord("s"):
                tts.toggle()
            elif key == ord("c"):
                transcript.clear()
    finally:
        # INVARIANT: Always release webcam, stop background TTS thread, and close windows cleanly
        cap.release()
        cv2.destroyAllWindows()
        detector.close()
        tts.stop()
        print("Application shut down cleanly.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-Time Sign Language Recognition App")
    parser.add_argument(
        "--config",
        default="configs/config.yaml",
        help="Path to YAML configuration file",
    )
    args = parser.parse_args()
    run_app(config_path=args.config)


if __name__ == "__main__":
    main()
