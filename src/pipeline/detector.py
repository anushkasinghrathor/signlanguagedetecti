"""
Hand Landmark Extractor and Normalizer Module
---------------------------------------------
Uses MediaPipe Hands to detect up to 2 hands, extract 21 3D landmarks per hand,
and perform wrist-relative scale and translation normalization.

# INVARIANT: Output feature vector must ALWAYS be a 1D float32 array of shape (126,).
# INVARIANT: Left Hand slots: [0:63], Right Hand slots: [63:126]. Missing hands are zero-padded.
"""

from typing import Tuple, List, Optional
import cv2
import numpy as np
import mediapipe as mp


def normalize_landmarks(pts: np.ndarray) -> np.ndarray:
    """
    Normalizes a single hand's 21 landmarks (shape: [21, 3]) for translation and scale invariance.
    
    1. Translation Invariance:
       Centers all points by subtracting the wrist position (Landmark 0):
       p'_i = p_i - p_wrist
       
    2. Scale Invariance:
       Divides coordinates by the Euclidean distance from the wrist (0) to the
       Middle Finger MCP joint (Landmark 9).
       # WHY: Landmark 9 (MCP base) provides a rigid skeletal scale anchor that does
       # not fluctuate when the user curls, bends, or wiggles their fingers.
    """
    if pts.shape != (21, 3):
        raise ValueError(f"Expected landmark array of shape (21, 3), got {pts.shape}")

    # Step 1: Center coordinates at wrist (origin)
    wrist = pts[0].copy()
    centered = pts - wrist

    # Step 2: Calculate scale distance (Wrist to Middle Finger MCP)
    # Fallback to max distance if Middle MCP distance is degenerate (< 1e-6)
    mcp_dist = float(np.linalg.norm(centered[9]))
    if mcp_dist < 1e-4:
        max_dist = float(np.max(np.linalg.norm(centered, axis=1)))
        scale = max_dist if max_dist > 1e-4 else 1.0
    else:
        scale = mcp_dist

    # Step 3: Divide by scale factor and flatten to 63 features
    normalized = centered / scale
    return normalized.flatten().astype(np.float32)


class HandDetector:
    """
    Wrapper around MediaPipe Hands providing real-time landmark extraction,
    scale-invariant normalization, velocity estimation, and visual rendering.
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
    ):
        self.max_num_hands = max_num_hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # State tracking for velocity estimation
        self._previous_feature_vector: Optional[np.ndarray] = None

    def process_frame(
        self, frame: np.ndarray, draw: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, int, float]:
        """
        Processes a single BGR video frame.

        Parameters:
            frame: Input image (BGR format from OpenCV)
            draw: Whether to draw landmarks on the returned annotated frame

        Returns:
            annotated_frame: Frame with skeletal landmarks drawn (if draw=True)
            feature_vector: Normalized 1D float32 array of shape (126,)
            hands_count: Number of hands detected (0, 1, or 2)
            velocity: Estimated Euclidean movement velocity between frames
        """
        # INVARIANT: Output feature vector size is fixed at 126
        feature_vector = np.zeros(126, dtype=np.float32)
        annotated_frame = frame.copy() if draw else frame
        hands_count = 0

        # MediaPipe expects RGB format
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Performance optimization: mark image as not writeable to pass by reference
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if results.multi_hand_landmarks and results.multi_handedness:
            hands_count = len(results.multi_hand_landmarks)

            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                # Extract 21 points (x, y, z)
                pts = np.array(
                    [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark],
                    dtype=np.float32,
                )
                norm_pts = normalize_landmarks(pts)

                # Determine hand label: 'Left' or 'Right'
                # Note: MediaPipe assumes mirrored selfie camera by default.
                hand_label = handedness.classification[0].label

                # INVARIANT: Left hand occupies [0:63], Right hand occupies [63:126]
                if hand_label == "Left":
                    feature_vector[0:63] = norm_pts
                else:
                    feature_vector[63:126] = norm_pts

                if draw:
                    self.mp_drawing.draw_landmarks(
                        annotated_frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style(),
                    )

        # Estimate landmark movement velocity relative to previous frame
        velocity = 0.0
        if self._previous_feature_vector is not None and hands_count > 0:
            diff = feature_vector - self._previous_feature_vector
            velocity = float(np.linalg.norm(diff) / np.sqrt(126))

        if hands_count > 0:
            self._previous_feature_vector = feature_vector.copy()
        else:
            self._previous_feature_vector = None

        return annotated_frame, feature_vector, hands_count, velocity

    def close(self):
        """Release MediaPipe resources gracefully."""
        self.hands.close()
