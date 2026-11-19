# DECISIONS LOG (Rationale & Architectural Choices)

> **Answers:** "Why did you do X instead of Y?"
> Log every non-trivial decision the AI and developer make.
> **Rule:** Draft the entry *before* writing or modifying the code.
> Always version-pin the model used for reasoning.

---

## D-001: Adopt "Defend What You Ship" (Whiteboard Edition v2)
- **Date:** 2026-11-02
- **Model:** Gemini 3.8 Flash High
- **Context:** Need a rigorous, defensible engineering methodology for AI-assisted development across current and future projects.
- **Options:**
  1. *Ad-hoc prompting without documentation:* Rely on raw chat logs and memory.
  2. *Standard PR reviews only:* Review code diffs after the AI writes them without structured rationale logs.
  3. *Defend What You Ship framework:* 25 habits, 4 defense questions, two lanes (PoC vs Customer Facing), pre-ship gate, and living docs (`HANDOVER`, `DECISIONS`, `FLOW`, `ARCHITECTURE`, etc.).
- **Chosen:** Option 3
- **Why:** Ad-hoc prompting loses context between sessions. Standard PRs miss the trade-offs and unverified assumptions. The Defend framework ensures the human remains the author and director of decisions, with whiteboard-level defensibility.
- **Trade-off:** Small initial documentation overhead per non-trivial change; saves hours of debugging and reverse-engineering later.
- **Revisit if:** Overhead exceeds demonstrable quality and clarity benefits on throwaway PoCs (in which case Lane A applies).

---

## D-002: Core Dependency Stack & Conda Environment `signenv`
- **Date:** 2026-11-02
- **Model:** Gemini 3.8 Flash High
- **Context:** Project Synopsis requires real-time hand landmark extraction, dual-model classification (MLP for static, LSTM for dynamic), offline TTS, and stable real-time operation in a dedicated Python 3.10 conda environment `signenv`.
- **Options:**
  1. *Global Python / venv with ad-hoc package installation:* Lightweight, but easily conflicts with other workspace packages.
  2. *Docker container:* High isolation, but introduces complex webcam hardware pass-through and audio latency on Windows.
  3. *Conda environment `signenv` (Python 3.10) + pinned requirements:* Native Windows webcam access, isolated C++ binary dependencies (OpenCV, MediaPipe), and offline SAPI5 TTS (`pyttsx3`).
- **Chosen:** Option 3
- **Why:** Conda `signenv` guarantees isolated native hardware execution for webcam and audio, while NumPy `<2.0.0` prevents known MediaPipe/PyTorch breaking changes.
- **Trade-off:** Requires explicit activation or `conda run -n signenv` invocation prefix for every command.
- **Revisit if:** Target shifts to web deployment or Dockerized cloud inference.

---

## D-003: 126-D Dual-Hand Feature Space & Velocity-Based Model Routing
- **Date:** 2026-11-02
- **Model:** Gemini 3.8 Flash High
- **Context:** Need to represent both 1-handed (A-Z) and 2-handed signs without dynamic tensor reshaping, and smoothly transition between static poses and dynamic motion gestures in real time.
- **Options:**
  1. *Single hand only (63 features) + manual hotkey toggle:* Simpler, but cannot recognize 2-handed signs and forces awkward user keyboard toggling.
  2. *Variable length landmark sequences without padding:* Saves memory for single hand, but breaks batch tensor operations and requires complex dynamic model heads.
  3. *Fixed 126-D dual-hand vector (2x21x3) + zero-padding + motion velocity routing (Chosen):* Deterministic vector shape, wrist-relative translation invariance, Euclidean scale normalization, and automatic stillness-vs-motion routing.
- **Chosen:** Option 3
- **Why:** Delivers unified input tensors across all ML/DL models; wrist centering removes camera distance and position bias; zero-padding cleanly handles single-hand poses.
- **Trade-off:** 63 zeros stored in feature vectors when only one hand is visible; minimal memory impact (<500 bytes per frame).
- **Revisit if:** Memory constraints in microcontrollers require dynamic sparse compression.

---

## D-004: Threaded Offline TTS Worker (`pyttsx3`) with Bounded Queue & Debounce
- **Date:** 2026-11-18
- **Model:** Gemini 3.8 Flash High
- **Context:** Real-time sign recognition must convert recognized text to audible speech without blocking or freezing the 30 FPS OpenCV capture and inference loop.
- **Options:**
  1. *Inline `pyttsx3.runAndWait()` on the main thread:* Simplest code, but blocks the video loop for 1-3 seconds per word, causing severe frame drops.
  2. *Cloud TTS (`gTTS` / online API):* Natural voices, but introduces network dependency, internet latency, and privacy/availability failure modes.
  3. *Dedicated daemon worker thread with `pyttsx3` (Windows SAPI5), bounded `queue.Queue(maxsize=3)`, and cooldown debouncing (Chosen):* Zero network dependency, non-blocking O(1) enqueue from the main video thread, and drops stale queued speech if signs occur faster than playback.
- **Chosen:** Option 3
- **Why:** Guarantees offline reliability and isolates blocking SAPI5 audio playback from the real-time OpenCV thread. Bounded queue prevents audio backlog lag, and a configurable cooldown (default 2.0s) stops continuous repetition of held signs.
- **Trade-off:** Robotic system SAPI5 voice quality and Windows COM initialization needed inside the worker thread (`CoInitialize`).
- **Revisit if:** Natural neural voices (e.g. Piper/Kokoro local ONNX TTS) are required for production accessibility.

---

## D-005: Sliding-Window Majority Smoothing & Smoothed Velocity Routing
- **Date:** 2026-11-18
- **Model:** Gemini 3.8 Flash High
- **Context:** Frame-by-frame ML predictions flicker during hand transitions, and raw single-frame hand velocity can spike from landmark jitter, causing unintended switching between static (MLP) and dynamic (LSTM) models.
- **Options:**
  1. *Raw per-frame argmax prediction:* Zero added latency, but causes severe text flickering and false TTS triggers during transitions.
  2. *Exponential Moving Average (EMA) on probability vectors:* Works well for a single model, but harder to combine cleanly across two models with different vocabularies (static vs dynamic).
  3. *Fixed `deque(maxlen=10)` majority-vote smoother (confidence $\ge 0.85$, consensus $\ge 6/10$) + 5-frame velocity moving average for AUTO routing (Chosen):* Model-agnostic, eliminates single-frame noise, resets cleanly when hands leave the frame, and supports manual override (`m` key).
- **Chosen:** Option 3
- **Why:** Works seamlessly across both MLP and LSTM label spaces, adds only ~0.2s latency at 30 FPS, and keeps screen text and voice output rock-steady.
- **Trade-off:** ~200ms confirmation delay before a new sign locks in; acceptable for clear assistive communication.
- **Revisit if:** Continuous fast fingerspelling requires sub-100ms response times (reduce window from 10 to 5 frames).

---

<!--
Template for next entries:

## D-00X: [Title]
- **Date:** YYYY-MM-DD
- **Model:** [e.g. Gemini 3.8 Flash High]
- **Context:** [Why does this decision need to be made?]
- **Options:**
  1) [Option 1]
  2) [Option 2]
  3) [Option 3]
- **Chosen:** [Option number]
- **Why:** [Specific justification why chosen won]
- **Trade-off:** [What cost, complexity, or downside was accepted?]
- **Revisit if:** [Condition or threshold that would trigger rethinking]
-->
