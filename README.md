# Real-Time Sign Language Recognition Using Computer Vision & Deep Learning

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Tests Passing](https://img.shields.io/badge/tests-17%20passed-brightgreen.svg)]()
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()
[![Methodology: Defend What You Ship](https://img.shields.io/badge/methodology-Defend%20What%20You%20Ship%20v2-orange.svg)](docs/defense/DEFENSE.md)

A real-time, low-latency sign language recognition desktop application that translates hand gestures captured via a standard webcam into on-screen text and audible speech using offline Text-to-Speech (TTS).

Developed based on the project synopsis submitted by **Kriti Pandey** and **Anushka Singh**.

---

## 1. System Architecture

```text
[ Webcam Stream ]
       │
       ▼
[ MediaPipe Hands ] ────────► 21 landmarks / hand (up to 2 hands)
       │
       ▼
[ Normalizer ] ─────────────► Wrist-centering & middle MCP scale invariance (126-D float vector)
       │
       ▼
[ Velocity-Based Router ]
       ├── (Low Velocity / Steady) ──► Static Classifier (Scikit-learn MLP)
       └── (Active Motion) ──────────► 30-Frame Temporal Buffer ──► Dynamic Classifier (PyTorch LSTM)
       │
       ▼
[ Prediction Smoother ] ────► 10-frame majority vote (>= 60% consensus, conf >= 0.85) + idle reset
       │
       ├──► [ OpenCV HUD Card ] ──► Real-time text display, confidence bar & FPS
       └──► [ Audio Worker ] ─────► Non-blocking background thread with pyttsx3 (SAPI5)
```

---

## 2. Supported Vocabulary

* **Static Gestures (Single-Frame MLP):** `A`, `B`, `C`, `ThumbsUp`, `Peace`
* **Dynamic Gestures (30-Frame Sequence LSTM):** `Hello`, `ThankYou`, `Yes`

---

## 3. Quick Start Guide

### Step 1: Environment Setup
Ensure you have Anaconda or Miniconda installed, then activate the dedicated environment:
```powershell
conda activate signenv
pip install -r requirements.txt
```

### Step 2: Run Tests (Verification)
Verify all mathematical invariants, model architectures, and TTS components:
```powershell
conda run -n signenv python -m pytest tests/ -v
```

### Step 3: Record Your Gesture Dataset
Launch the interactive webcam data collector:
```powershell
# 1. Record static signs (press SPACE to start countdown):
conda run -n signenv python -m src.data.collector --mode static

# 2. Record dynamic motion signs (press SPACE to start countdown):
conda run -n signenv python -m src.data.collector --mode dynamic
```

### Step 4: Check Dataset Health
```powershell
conda run -n signenv python -m src.data.inspect_data
```

### Step 5: Train the Models
```powershell
# Train Static MLP:
conda run -n signenv python -m src.models.train_static

# Train Dynamic PyTorch LSTM:
conda run -n signenv python -m src.models.train_dynamic
```

### Step 6: Launch the Live Desktop Application
```powershell
conda run -n signenv python -m src.app
```

#### In-App Keyboard Controls:
* **`M`**: Cycle routing mode (`AUTO` $\rightarrow$ `STATIC` $\rightarrow$ `DYNAMIC`)
* **`S`**: Toggle Text-to-Speech audio `ON` / `MUTED`
* **`C`**: Clear recent word history transcript
* **`Q`**: Quit application safely and release webcam

---

## 4. Benchmark & Performance Budget

Measurements taken on local hardware inside `signenv`:
* **Static MLP Inference:** `~0.080 ms` (target < 15 ms)
* **Dynamic PyTorch LSTM Inference:** `~1.088 ms` (target < 15 ms)
* **MediaPipe Landmark Extraction:** `~17.27 ms`
* **Total Pipeline Latency:** `~18.37 ms` (**~54 to 57 FPS on CPU**)

Run the benchmark anytime:
```powershell
conda run -n signenv python scripts/benchmark_latency.py
```

---

## 5. Project Layout

```text
signlanguagedetection/
├── configs/
│   └── config.yaml             # Central configuration (camera, vocabulary, thresholds)
├── data/                       # Recorded dataset storage
│   ├── static/                 # Static single-frame CSV datasets
│   └── dynamic/                # Dynamic 30-frame sequence .npy files
├── docs/                       # Living Whiteboard Architecture & Defense Documentation
│   ├── ARCHITECTURE.md         # System map and trust boundaries
│   ├── CONSTRAINTS.md          # Hard boundaries (never/always/only)
│   ├── DATA.md                 # 126-D data structures and memory layout
│   ├── DECISIONS.md            # Rationale log (D-001 through D-005)
│   ├── FAILURE.md              # Failure modes and resilience matrix
│   ├── FLOW.md                 # End-to-end execution flow
│   ├── HANDOVER.md             # Session continuity log
│   ├── TESTING.md              # Automated commands and manual customer path
│   └── defense/
│       ├── DEFENSE.md          # Capstone 1-page whiteboard brief
│       ├── PRE_SHIP_GATE.md    # 14-item pre-ship checklist
│       └── WHITEBOARD_DRILL.md # 12 defense drill questions
├── models/                     # Trained model weights & label mappings
├── scripts/
│   └── benchmark_latency.py    # Latency and FPS benchmark
├── src/                        # Core Application
│   ├── data/                   # collector.py, inspect_data.py
│   ├── models/                 # lstm.py, train_static.py, train_dynamic.py
│   ├── pipeline/               # detector.py, smoother.py
│   ├── tts/                    # speaker.py (non-blocking threaded pyttsx3)
│   └── app.py                  # Main real-time desktop application
├── tests/                      # PyTest automated test suite (17 passed)
├── .gitignore
├── AGENTS.md                   # AI governance rules (Defend What You Ship)
├── requirements.txt            # Pinned dependencies
└── tasks.md                    # Detailed progress and roadmap tracker
```

---

## 6. Engineering Governance

This project adheres to the **"Defend What You Ship (Whiteboard Edition v2)"** methodology. Every architectural decision, trade-off, and failure mode is documented in [docs/](docs/) and can be defended at a whiteboard without notes.
