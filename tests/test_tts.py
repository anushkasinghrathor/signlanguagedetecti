"""
Unit Tests for Non-Blocking TextToSpeechWorker
----------------------------------------------
Verifies non-blocking dispatch, cooldown debouncing, mute/toggle behavior,
bounded queue overflow handling, and real pyttsx3 initialization in signenv.
"""

import threading
import time
from typing import List

from src.tts.speaker import TextToSpeechWorker


def test_tts_non_blocking_and_delivery():
    """Verify speak() returns immediately while slow playback runs in background."""
    spoken: List[str] = []
    done_event = threading.Event()

    def slow_backend(text: str) -> None:
        time.sleep(0.15)
        spoken.append(text)
        done_event.set()

    with TextToSpeechWorker(cooldown_seconds=1.0, speak_callback=slow_backend) as tts:
        t0 = time.monotonic()
        queued = tts.speak("Hello")
        elapsed_ms = (time.monotonic() - t0) * 1000.0

        assert queued is True
        # INVARIANT: Main thread must never block waiting for audio playback
        assert elapsed_ms < 50.0, f"speak() blocked main thread for {elapsed_ms:.1f}ms"
        assert done_event.wait(timeout=1.0), "Background worker did not deliver speech"
        assert spoken == ["Hello"]


def test_tts_debounce_cooldown():
    """Identical words within cooldown are suppressed; different words speak immediately."""
    spoken: List[str] = []
    gate = threading.Event()

    def record_backend(text: str) -> None:
        spoken.append(text)
        if len(spoken) >= 3:
            gate.set()

    with TextToSpeechWorker(cooldown_seconds=0.25, speak_callback=record_backend) as tts:
        assert tts.speak("Hello") is True
        # Immediate repeat must be debounced
        assert tts.speak("Hello") is False
        # Different word should bypass same-word debounce
        assert tts.speak("Thank You") is True
        # Wait past cooldown, then same word should be allowed again
        time.sleep(0.30)
        assert tts.speak("Thank You") is True

        assert gate.wait(timeout=1.0)
        assert spoken == ["Hello", "Thank You", "Thank You"]


def test_tts_mute_and_empty_inputs():
    """Muted worker and blank/whitespace strings must never enqueue speech."""
    spoken: List[str] = []

    with TextToSpeechWorker(enabled=False, speak_callback=spoken.append) as tts:
        assert tts.speak("Hello") is False
        assert tts.toggle() is True
        assert tts.speak("") is False
        assert tts.speak("   ") is False
        assert tts.speak("Yes") is True
        time.sleep(0.1)

    assert spoken == ["Yes"]


def test_tts_bounded_queue_evicts_stale_items():
    """Flooding the worker must never block or raise queue.Full."""
    block_first = threading.Event()
    spoken: List[str] = []

    def blocking_backend(text: str) -> None:
        if text == "first":
            block_first.wait(timeout=0.5)
        spoken.append(text)

    with TextToSpeechWorker(
        cooldown_seconds=0.0, max_queue_size=2, speak_callback=blocking_backend
    ) as tts:
        assert tts.speak("first") is True
        time.sleep(0.05)  # Let worker pick up "first" and block on it

        # Rapidly flood 5 messages into a maxsize=2 queue
        for word in ["w1", "w2", "w3", "w4", "w5"]:
            assert tts.speak(word) is True

        block_first.set()
        time.sleep(0.2)

    assert "first" in spoken
    assert "w5" in spoken  # Latest utterance is preserved
    assert len(spoken) <= 4


def test_tts_real_pyttsx3_initialization_and_shutdown():
    """Verify real pyttsx3 engine starts cleanly in worker thread and exits cleanly."""
    with TextToSpeechWorker(rate=160, volume=0.0, cooldown_seconds=1.0) as tts:
        assert tts.engine_error is None, f"pyttsx3 failed to init: {tts.engine_error}"
