"""
Non-Blocking Text-to-Speech (TTS) Worker
----------------------------------------
Runs pyttsx3 (Windows SAPI5 / offline TTS) inside a dedicated background daemon
thread decoupled from the OpenCV video loop via a bounded thread-safe queue.

# INVARIANT: speak() must NEVER block the caller (main OpenCV capture/inference thread).
# INVARIANT: pyttsx3 engine is initialized and driven strictly inside the worker thread.
"""

import logging
import queue
import threading
import time
from typing import Callable, Optional

import pyttsx3

logger = logging.getLogger(__name__)


class TextToSpeechWorker:
    """
    Thread-safe, non-blocking TTS engine with speech debouncing and bounded queueing.
    """

    def __init__(
        self,
        rate: int = 160,
        volume: float = 1.0,
        cooldown_seconds: float = 2.0,
        enabled: bool = True,
        max_queue_size: int = 3,
        speak_callback: Optional[Callable[[str], None]] = None,
    ):
        self.rate = rate
        self.volume = max(0.0, min(1.0, float(volume)))
        self.cooldown_seconds = max(0.0, float(cooldown_seconds))
        self._enabled = bool(enabled)
        self._speak_callback = speak_callback

        # Bounded queue prevents stale spoken words from piling up if signs occur rapidly
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=max(1, max_queue_size))
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()

        self._last_spoken_text: Optional[str] = None
        self._last_spoken_time: float = 0.0
        self._engine_error: Optional[str] = None

        self._thread = threading.Thread(
            target=self._worker_loop,
            name="SignLanguageTTSWorker",
            daemon=True,
        )
        self._thread.start()
        # Wait briefly so engine init issues surface predictably without stalling startup
        self._ready_event.wait(timeout=2.0)

    @property
    def enabled(self) -> bool:
        with self._state_lock:
            return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        with self._state_lock:
            self._enabled = bool(value)

    @property
    def engine_error(self) -> Optional[str]:
        return self._engine_error

    def toggle(self) -> bool:
        """Toggles audio output on/off safely and returns the new enabled state."""
        with self._state_lock:
            self._enabled = not self._enabled
            return self._enabled

    def speak(self, text: str) -> bool:
        """
        Non-blocking request to speak `text`.

        Applies empty-string filtering, mute check, and identical-word cooldown debouncing.
        Returns True if enqueued for playback, False if filtered/debounced/stopped.
        """
        if self._stop_event.is_set():
            return False

        cleaned = text.strip() if isinstance(text, str) else ""
        if not cleaned:
            return False

        now = time.monotonic()
        with self._state_lock:
            if not self._enabled:
                return False

            # Debounce identical consecutive utterances within the cooldown window
            if (
                self._last_spoken_text == cleaned
                and (now - self._last_spoken_time) < self.cooldown_seconds
            ):
                return False

            self._last_spoken_text = cleaned
            self._last_spoken_time = now

        # WHY: If queue is full, evict the oldest pending utterance so live speech stays current
        while True:
            try:
                self._queue.put_nowait(cleaned)
                return True
            except queue.Full:
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break

        return False

    def _init_com_if_windows(self) -> bool:
        """
        Initializes Windows COM apartment on the worker thread for SAPI5.
        # WHY: On Windows, pyttsx3 uses SAPI5 COM objects which are thread-affine;
        # calling CoInitialize inside the worker thread prevents COM initialization errors.
        """
        try:
            import comtypes  # type: ignore

            comtypes.CoInitialize()
            return True
        except Exception:
            return False

    def _uninit_com_if_windows(self, initialized: bool) -> None:
        if not initialized:
            return
        try:
            import comtypes  # type: ignore

            comtypes.CoUninitialize()
        except Exception:
            pass

    def _worker_loop(self) -> None:
        """Background thread loop consuming queued phrases and synthesizing speech."""
        com_initialized = False
        engine = None

        if self._speak_callback is None:
            com_initialized = self._init_com_if_windows()
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
            except Exception as exc:
                # Fail gracefully: text HUD keeps working even if audio hardware is unavailable
                self._engine_error = str(exc)
                logger.warning("TTS engine initialization failed: %s", exc)
                engine = None

        self._ready_event.set()

        try:
            while not self._stop_event.is_set():
                try:
                    item = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                try:
                    # Sentinel None signals clean shutdown
                    if item is None:
                        break

                    if self._speak_callback is not None:
                        self._speak_callback(item)
                    elif engine is not None:
                        # Runs inside the dedicated worker thread so main OpenCV loop never blocks
                        engine.say(item)
                        engine.runAndWait()
                except Exception as exc:
                    logger.warning("TTS playback error for '%s': %s", item, exc)
                finally:
                    self._queue.task_done()
        finally:
            if engine is not None:
                try:
                    engine.stop()
                except Exception:
                    pass
            self._uninit_com_if_windows(com_initialized)

    def stop(self, timeout: float = 2.0) -> None:
        """Signals the background worker to exit cleanly and joins the thread."""
        if self._stop_event.is_set():
            return

        self._stop_event.set()

        # Drain queued items so shutdown sentinel is processed promptly
        while True:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

        if self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def __enter__(self) -> "TextToSpeechWorker":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
