"""
Unit Tests for HandDetector and Landmark Normalization Pipeline
--------------------------------------------------------------
Verifies scale invariance, translation invariance, feature dimensions,
and empty-frame edge cases.
"""

import numpy as np
import pytest
from src.pipeline.detector import normalize_landmarks, HandDetector


def test_normalize_landmarks_dimensions():
    """Verify that normalize_landmarks accepts (21, 3) and outputs (63,)."""
    # Create synthetic hand coordinates
    pts = np.random.rand(21, 3).astype(np.float32)
    # Ensure Middle MCP (index 9) is separated from wrist (index 0)
    pts[9] = pts[0] + np.array([0.2, 0.3, 0.1], dtype=np.float32)

    norm = normalize_landmarks(pts)
    assert norm.shape == (63,)
    assert norm.dtype == np.float32
    # The wrist (origin) after normalization must be at (0, 0, 0)
    assert np.allclose(norm[0:3], [0.0, 0.0, 0.0], atol=1e-6)


def test_normalize_landmarks_translation_invariance():
    """
    CRITICAL INVARIANT TEST:
    Moving the hand across the frame (adding arbitrary [dx, dy, dz] offsets)
    must produce identical normalized features.
    """
    pts = np.random.rand(21, 3).astype(np.float32)
    pts[9] = pts[0] + np.array([0.2, 0.3, 0.1], dtype=np.float32)

    norm_original = normalize_landmarks(pts)

    # Apply substantial translation offset
    offset = np.array([150.5, -82.3, 45.0], dtype=np.float32)
    pts_translated = pts + offset

    norm_translated = normalize_landmarks(pts_translated)
    assert np.allclose(norm_original, norm_translated, atol=1e-5), (
        "Normalization must be translation invariant"
    )


def test_normalize_landmarks_scale_invariance():
    """
    CRITICAL INVARIANT TEST:
    Scaling the hand (user moves closer/further from the lens)
    must produce identical normalized features.
    """
    pts = np.random.rand(21, 3).astype(np.float32)
    pts[9] = pts[0] + np.array([0.15, 0.25, 0.05], dtype=np.float32)

    norm_original = normalize_landmarks(pts)

    # User moves 3x closer to camera
    pts_scaled = pts * 3.0
    norm_scaled = normalize_landmarks(pts_scaled)

    assert np.allclose(norm_original, norm_scaled, atol=1e-5), (
        "Normalization must be scale invariant"
    )


def test_normalize_landmarks_invalid_shape():
    """Verify that malformed landmark inputs raise ValueError."""
    bad_pts = np.zeros((20, 3), dtype=np.float32)
    with pytest.raises(ValueError):
        normalize_landmarks(bad_pts)


def test_hand_detector_empty_frame():
    """
    Verify behavior on blank / empty frames:
    - Must detect 0 hands
    - Feature vector must be exactly 126 zeros
    - Must not crash or throw exceptions
    """
    detector = HandDetector(static_image_mode=True)
    try:
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        annotated_frame, features, count, velocity = detector.process_frame(blank_frame)

        assert count == 0
        assert features.shape == (126,)
        assert np.all(features == 0.0)
        assert velocity == 0.0
        assert annotated_frame.shape == (480, 640, 3)
    finally:
        detector.close()
