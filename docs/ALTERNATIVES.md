# ALTERNATIVES (Rejected Options & Trade-Off Matrix)

> **Answers:** "Why did you do X instead of Y?"
> Defending a decision requires remembering the alternatives you turned down.
> Without alternatives, every choice sounds like the only possible one (a major red flag).

---

## 1. Gesture Tracking Approach

| Option | Pros | Cons / Cost | Revisit If |
| :--- | :--- | :--- | :--- |
| **MediaPipe Keypoints + LSTM/Transformer (Chosen)** | Lightweight, real-time on CPU, robust to background noise and lighting variations. | Dependent on keypoint detector accuracy; misses fine texture details. | Gesture nuances require skin texture or raw depth maps. |
| **End-to-End 3D-CNN on Raw Video Frames** | Captures all visual texture and spatial context directly. | Very heavy compute requirements; slow inference; prone to overfitting on backgrounds. | Dedicated edge GPUs or cloud TPUs become universally available. |
| **Traditional Optical Flow + Handcrafted Features** | Extremely fast, zero ML framework dependency. | Fragile, breaks under complex backgrounds, cannot handle temporal variations well. | Running on extreme ultra-low-power microcontrollers (e.g. Arduino). |

---

## 2. Real-Time Inference Engine

| Option | Pros | Cons / Cost | Revisit If |
| :--- | :--- | :--- | :--- |
| **ONNX Runtime (Chosen)** | Cross-platform, hardware acceleration (DirectML/CUDA/CPU), optimized execution. | Requires exporting model step and verifying operator compatibility. | Rapid training iteration where pure PyTorch is needed during exploration. |
| **Raw PyTorch Python Runtime** | Zero export step, easiest to prototype in research. | Higher memory footprint, slower startup, Python GIL bottlenecks. | Strictly exploratory research / offline dataset evaluation. |
| **TensorFlow Lite (TFLite)** | Great mobile/embedded support. | Operator constraints; cumbersome build on desktop environments. | Targeting mobile devices (Android/iOS apps). |

---

<!--
Template for documenting new alternatives:

## [Decision Area]
- **Chosen:** [Approach chosen]
- **Rejected Option 1:** [Name]
  - *Cost/Risk:* [Why was it rejected?]
  - *Gave Up:* [What advantage did we sacrifice?]
  - *Revisit if:* [What condition would make this option viable?]
-->
