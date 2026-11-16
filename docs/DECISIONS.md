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
