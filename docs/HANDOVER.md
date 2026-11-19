# HANDOVER

> **Protocol:** The AI reads this file first at the start of every session, and updates it last before the session ends. Add the newest session on top.

## Latest session: 2026-11-18 (model: Gemini 3.8 Flash High)
**Done:**
- Logged Decisions `D-004` (Threaded TTS worker) and `D-005` (Sliding-window majority smoother & smoothed velocity routing) in `docs/DECISIONS.md`.
- Completed Phase 4 (`src/tts/speaker.py`, `tests/test_tts.py`).
- Completed Phase 5 & Task 2.3 (`src/pipeline/smoother.py`, `src/app.py`, `src/data/inspect_data.py`, `tests/test_smoother.py`).
- Verified full automated test suite in `signenv`: `17 passed in 7.07s` (zero failures).
- Completed Task 3.3 (`scripts/benchmark_latency.py`): Static MLP `0.080ms`, Dynamic PyTorch LSTM `1.088ms` (CPU), MediaPipe `17.27ms` (~54–57 FPS end-to-end).
- 100% of core application code and benchmarks are built and verified.

**In progress:**
- User webcam dataset recording (`src/data/collector.py`) and model training (`train_static.py`, `train_dynamic.py`).

**Broken or risky:**
- `models/static_mlp.joblib` and `models/dynamic_lstm.pt` do not exist until the user records real webcam gestures and runs training (app handles missing models safely without crashing).

**Next:**
- Record static & dynamic gestures on webcam (`collector.py`).
- Inspect dataset (`inspect_data.py`), train MLP & LSTM models (`train_static.py`, `train_dynamic.py`), and launch the live desktop app (`python -m src.app`).
- Complete Pre-Ship Gate & Whiteboard Drill (Phase 6).

**Do not touch:**
- `docs/CONSTRAINTS.md` rules; strict confirmation before file edits.

---

## Session: 2026-11-16 (model: Gemini 3.8 Flash High)
**Done:**
- Resolved MediaPipe solutions availability by pinning `mediapipe==0.10.14` and stable `pytest==8.4.2` in `signenv`.
- Executed the real-time detection pipeline directly on the live webcam in terminal; verified 15 real frames processed at ~20-35ms latency (~30-50 FPS) with sample frame saved.
- Completed Phase 1 (Foundation & Landmark Extraction) and Phase 2.1 (Interactive Dataset Collector).
- Completed Phase 3.1 & 3.2: Implemented static MLP trainer (`src/models/train_static.py`), dynamic PyTorch LSTM (`src/models/lstm.py`), and dynamic training loop (`src/models/train_dynamic.py`).
- Verified 100% of test suite passes (`7 passed in 8.47s` in `tests/test_detector.py` and `tests/test_models.py`).

**In progress:**
- Phase 4: Non-blocking Text-to-Speech (TTS) Engine (`src/tts/speaker.py`).
- Recording training dataset via webcam (`src/data/collector.py`).

**Broken or risky:**
- None.

**Next:**
- Implement non-blocking threaded `pyttsx3` audio worker (Phase 4).
- Implement real-time inference application with HUD overlay (Phase 5).

**Do not touch:**
- `docs/CONSTRAINTS.md` rules.

---

## Session: 2026-11-02 (model: Gemini 3.8 Flash High)
**Done:**
- Initialized repository with "Defend What You Ship" (Whiteboard Edition v2) governance and documentation structure.
- Created `AGENTS.md` and updated `CONSTRAINTS.md` enforcing `signenv` (Python 3.10) and strict human confirmation before changes.
- Created `requirements.txt` and successfully installed dependencies into `signenv`.
- Smoke-test verified imports of `cv2`, `mediapipe`, `torch`, `sklearn`, and `pyttsx3` with exit code 0.
- Logged decision `D-002` in `docs/DECISIONS.md`.

**In progress:**
- Defining project structure, gesture vocabulary, and dataset collection tool.

**Broken or risky:**
- None.

**Next:**
- Scaffolding project code structure (`src/`, `data/`, `models/`, `configs/`).
- Building the MediaPipe landmark extractor and dataset recorder tool.

**Do not touch:**
- `docs/CONSTRAINTS.md` rules unless explicitly authorized.

---
*Read first:* `docs/ARCHITECTURE.md`, `docs/CONSTRAINTS.md`
