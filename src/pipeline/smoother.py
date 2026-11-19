"""
Temporal Prediction Smoother & Stability Filter
-----------------------------------------------
Eliminates single-frame prediction flickering using confidence thresholding,
a fixed-size sliding-window majority vote, and idle-frame reset logic.

# INVARIANT: History buffer size is bounded to `window_size` via collections.deque.
# INVARIANT: No prediction with confidence < confidence_threshold can ever trigger output.
"""

from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Optional, Tuple


@dataclass(frozen=True)
class SmoothedPrediction:
    """Stable prediction result emitted to the HUD and TTS worker."""

    label: str
    confidence: float
    is_new_trigger: bool


class PredictionSmoother:
    """
    Combines confidence gating and temporal majority voting to stabilize live sign predictions.
    """

    IDLE_LABEL = "Idle"

    def __init__(
        self,
        window_size: int = 10,
        min_consensus: int = 6,
        confidence_threshold: float = 0.85,
        idle_reset_frames: int = 3,
    ):
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        if not (1 <= min_consensus <= window_size):
            raise ValueError("min_consensus must be between 1 and window_size")
        if not (0.0 <= confidence_threshold <= 1.0):
            raise ValueError("confidence_threshold must be in [0.0, 1.0]")

        self.window_size = window_size
        self.min_consensus = min_consensus
        self.confidence_threshold = confidence_threshold
        self.idle_reset_frames = max(1, idle_reset_frames)

        # Stores (label_or_None, confidence) for the last N frames
        self._window: Deque[Tuple[Optional[str], float]] = deque(maxlen=window_size)
        self._empty_hand_streak: int = 0
        self._last_emitted_label: str = self.IDLE_LABEL

    def reset(self) -> None:
        """Clears sliding window and returns smoother to Idle state."""
        self._window.clear()
        self._empty_hand_streak = 0
        self._last_emitted_label = self.IDLE_LABEL

    def update(
        self,
        raw_label: Optional[str],
        confidence: float,
        hands_detected: int = 1,
    ) -> SmoothedPrediction:
        """
        Ingests one frame's raw prediction and returns the stabilized prediction.

        Args:
            raw_label: Class name predicted by MLP or LSTM (or None if unavailable).
            confidence: Predicted class probability in [0.0, 1.0].
            hands_detected: Number of hands currently visible in the frame.

        Returns:
            SmoothedPrediction(label, confidence, is_new_trigger)
        """
        # Handle hands leaving the frame with a short grace streak
        # WHY: A single-frame MediaPipe tracking drop should not wipe a held sign,
        # but dropping hands for ~0.1s (3 frames) cleanly resets state so the same
        # sign can be performed again deliberately.
        if hands_detected <= 0:
            self._empty_hand_streak += 1
            if self._empty_hand_streak >= self.idle_reset_frames:
                self.reset()
                return SmoothedPrediction(self.IDLE_LABEL, 0.0, False)
            return SmoothedPrediction(self._last_emitted_label, 0.0, False)

        self._empty_hand_streak = 0

        # Confidence filter: treat uncertain frames as non-votes (None)
        accepted_label = (
            raw_label
            if (raw_label is not None and confidence >= self.confidence_threshold)
            else None
        )
        self._window.append((accepted_label, float(confidence)))

        # Count votes strictly among confident predictions in the sliding window
        valid_votes = [lbl for lbl, _ in self._window if lbl is not None]
        if not valid_votes:
            self._last_emitted_label = self.IDLE_LABEL
            return SmoothedPrediction(self.IDLE_LABEL, 0.0, False)

        top_label, top_count = Counter(valid_votes).most_common(1)[0]

        if top_count >= self.min_consensus:
            matching_confs = [conf for lbl, conf in self._window if lbl == top_label]
            avg_conf = sum(matching_confs) / len(matching_confs)
            is_new = top_label != self._last_emitted_label
            self._last_emitted_label = top_label
            return SmoothedPrediction(top_label, avg_conf, is_new)

        # Not enough consensus yet: hold steady without triggering false switches
        return SmoothedPrediction(self._last_emitted_label, 0.0, False)
