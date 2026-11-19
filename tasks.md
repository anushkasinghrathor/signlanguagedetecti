# TASKS & IMPLEMENTATION PLAN: Real-Time Sign Language Recognition

> **Methodology:** Defend What You Ship (Whiteboard Edition v2)  
> **Environment:** `signenv` (Conda, Python 3.10)  
> **Architecture:** MediaPipe Hands + Dual-Model (MLP for static, PyTorch LSTM for dynamic) + Threaded `pyttsx3` TTS

---

## Phase 1: Architectural Foundation & Landmark Extraction
- [x] **Task 1.1:** Environment setup in `signenv` with pinned dependencies (`opencv-python`, `mediapipe`, `torch`, `scikit-learn`, `pyttsx3`, `pandas`, `numpy<2.0.0`).
- [x] **Task 1.2:** Establish project governance docs (`AGENTS.md`, `CONSTRAINTS.md`, `DECISIONS.md`, `HANDOVER.md`).
- [x] **Task 1.3:** Create project configuration file (`configs/config.yaml`) defining camera resolution, FPS targets, confidence thresholds, and gesture vocabulary.
- [x] **Task 1.4:** Build modular MediaPipe landmark extractor (`src/pipeline/detector.py`) with:
  - Support for up to 2 hands (left & right).
  - Wrist-relative translation centering: $\mathbf{p}' = \mathbf{p} - \mathbf{p}_{\text{wrist}}$.
  - Middle finger MCP/tip scale normalization for distance invariance.
  - Consistent feature vector padding (126 dimensions: 2 hands × 21 landmarks × 3 coords).
- [x] **Task 1.5:** Write automated unit tests (`tests/test_detector.py`) verifying landmark dimension consistency and normalization math on synthetic frames.

---

## Phase 2: Data Collection & Dataset Curation
- [x] **Task 2.1:** Implement interactive data recorder CLI (`src/data/collector.py`):
  - Live video feed showing landmark skeleton overlays and countdown timer.
  - Mode A: Static snapshot collector (captures single-frame normalized vectors into `data/static/<gesture_name>.csv`).
  - Mode B: Dynamic sequence collector (captures sliding windows of 30 frames into `data/dynamic/<gesture_name>/sequence_X.npy`).
- [ ] **Task 2.2:** Collect baseline dataset across initial gesture vocabulary:
  - Static signs: `A`, `B`, `C`, `ThumbsUp`, `Peace`.
  - Dynamic signs: `Hello`, `ThankYou`, `Yes`, `No`.
- [x] **Task 2.3:** Implement data validation & inspection script (`src/data/inspect_data.py`) to verify class balance, absence of NaN/infinite coordinates, and sequence lengths.

---

## Phase 3: Model Architecture & Training Pipelines
- [x] **Task 3.1:** **Static Classifier (MLP):**
  - Implement training script (`src/models/train_static.py`) using Scikit-learn MLP / PyTorch MLP.
  - Input: 126-D normalized landmark vector.
  - Output: Class probabilities for static signs.
  - Save model weights (`models/static_mlp.joblib` or `.pt`) and evaluation report (accuracy, confusion matrix).
- [x] **Task 3.2:** **Dynamic Classifier (PyTorch LSTM):**
  - Implement PyTorch LSTM architecture (`src/models/lstm.py`):
    - Input shape: `(batch_size, 30_frames, 126_features)`.
    - Stacked 2-layer LSTM with dropout (0.2) + Dense linear classification head.
  - Implement training loop (`src/models/train_dynamic.py`) with Adam optimizer, Cross-Entropy Loss, and validation checkpointing.
  - Save best model weights (`models/dynamic_lstm.pt`).
- [x] **Task 3.3:** Export models and evaluate latency budget (`scripts/benchmark_latency.py` verified: Static MLP `0.080ms`, Dynamic LSTM `1.088ms` — both well under 15ms target; full pipeline ~54–57 FPS on CPU).

---

## Phase 4: Non-Blocking Text-to-Speech (TTS) Engine
- [x] **Task 4.1:** Build thread-safe audio worker (`src/tts/speaker.py`):
  - Initializes `pyttsx3` (with Windows COM `CoInitialize`) inside a dedicated background daemon thread.
  - Implements bounded thread-safe `queue.Queue(maxsize=3)` to decouple audio synthesis from OpenCV video loop without backlog lag.
- [x] **Task 4.2:** Implement speech debounce logic to prevent repeating identical signs continuously:
  - Minimum cooldown period (e.g. 2.0 seconds) between spoken utterances of the same word.
- [x] **Task 4.3:** Unit test TTS worker independently (`tests/test_tts.py`).

---

## Phase 5: Real-Time Desktop Application & Prediction Stability
- [x] **Task 5.1:** Implement prediction smoother (`src/pipeline/smoother.py`):
  - Confidence threshold filtering (e.g., minimum probability $\ge 0.85$).
  - Moving-window majority vote / temporal debounce over the last 10 predictions to eliminate single-frame flickering.
  - Idle/transition detector when hands leave the frame or rest.
- [x] **Task 5.2:** Build main desktop application (`src/app.py`):
  - OpenCV real-time capture and HUD display.
  - Visual cards: Detected sign name, confidence percentage bar, current FPS indicator, and landmark wireframe.
  - Audio trigger sending clean recognized words to TTS worker.
  - Keyboard shortcuts: `q` to quit safely, `m` to toggle model mode (static vs dynamic), `s` to toggle sound on/off.
- [x] **Task 5.3:** Ensure graceful resource shutdown (release webcam device, terminate audio worker thread, close OpenCV windows).

---

## Phase 6: Verification, Whiteboard Drill & Pre-Ship Gate
- [x] **Task 6.1:** Run automated test suite (`pytest tests/ -v`) and verify real console outputs.
- [ ] **Task 6.2:** Conduct manual end-to-end customer trial path (startup -> sign recognition -> screen text -> audio voice -> clean exit).
- [ ] **Task 6.3:** Complete the 14-item [PRE_SHIP_GATE.md](file:///c:/Study/signlanguagedetection/docs/defense/PRE_SHIP_GATE.md).
- [ ] **Task 6.4:** Conduct the 12-question Whiteboard Drill ([WHITEBOARD_DRILL.md](file:///c:/Study/signlanguagedetection/docs/defense/WHITEBOARD_DRILL.md)) to guarantee full defensibility.
