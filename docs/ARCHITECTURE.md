# ARCHITECTURE (System Map)

> **Answers:** All Four Defense Questions (Big Picture).
> Keep this document to 1 page. Maps modules, data flow, and trust boundaries so the AI and engineers don't re-derive the system every session.

## 1. System Overview

```
[ Camera / Video Source ]  ---> ( Trust Boundary 1: Raw Hardware Input )
            │
            ▼
[ Frame Preprocessor ]     ---> ( Resize, Normalize, Landmark Extraction e.g., MediaPipe )
            │
            ▼
[ Feature Extraction ]     ---> ( Keypoints / Sequence Vector: Hand, Pose, Face )
            │
            ▼
[ Classifier / ML Model ]  ---> ( Real-time Inference Engine: PyTorch / ONNX / TFLite )
            │
            ▼
[ Post-Processing ]        ---> ( Smoothing / Temporal Filtering / Debounce )
            │
            ▼
[ Output Layer / UI ]      ---> ( Text translation, Audio TTS, or Web display )
```

## 2. Core Modules & Responsibilities

| Module | Purpose | Ownership / Dependencies |
| :--- | :--- | :--- |
| **Input Pipeline** | Ingests video frames from webcam, video file, or network stream. | OpenCV / Browser WebRTC |
| **Pre-processor** | Landmark / keypoint detection and coordinate normalization. | MediaPipe / Custom extractor |
| **Model Runtime** | Executes inference over temporal windows of gestures. | ONNXRuntime / PyTorch / TensorFlow |
| **Output / Translation** | Maps token predictions to readable words, sentences, or speech. | Language model / Lookup dictionary |

## 3. Trust Boundaries

1. **Camera / Video Stream (Raw External Input):** Any video feed can send corrupt frames, unexpected resolutions, zero-byte frames, or malicious video containers. Must validate dimensions and frame rates.
2. **User Input / Control APIs:** If exposing an API or web interface, enforce strict request validation, rate limiting, and safe payload sizes.
