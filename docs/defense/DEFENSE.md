# DEFENSE: Sign Language Detection System

> **Capstone Whiteboard Cheat Sheet**
> Answers all four questions in your own words.
> Draft this after the build and before the ship. Re-read before every customer-facing release.

## What it does (2 sentences)
A real-time sign language recognition application that captures video input, extracts hand and body landmarks, and predicts sign language gestures to produce text and speech translations. It enables seamless communication for deaf and hard-of-hearing individuals with low latency on commodity hardware.

## How it works (sketch the flow)
Video stream -> OpenCV frame extraction -> MediaPipe landmark localization (21 hand keypoints) -> Coordinate normalization relative to wrist -> 30-frame temporal sliding window -> Neural network classifier (LSTM / Transformer / ONNX) -> Confidence threshold & temporal debouncing filter -> UI text display & audio output.

## Key decisions and why X over Y
- **Keypoint-based detection over raw video 3D-CNN:** Keypoint extraction eliminates background noise, lighting shifts, and skin-tone bias while running real-time on CPU, whereas 3D-CNN requires prohibitive GPU resources.
- **ONNX Runtime over native Python PyTorch:** ONNX Runtime delivers 2-3x lower inference latency, eliminates Python GIL contention, and provides hardware acceleration across OS platforms.

## Data structures and why
- **Fixed-size circular buffer (`deque(maxlen=30)`):** O(1) appending and automatic eviction of stale frames without reallocation overhead.
- **Normalized float array `(21, 3)`:** Vectorized array enabling SIMD spatial normalization in sub-millisecond execution time.

## How a malicious actor could abuse it
- Feeding rapid high-resolution streams or corrupted video chunks to cause denial-of-service / memory leaks. Mitigated by strict frame size caps (downscaling to 640x480) and frame rate throttle.
- Injecting rapid contradictory gestures to trigger flickering UI states. Mitigated by temporal smoothing and confidence hysteresis filters.

## Where it fails and how we notice
- **Low-light / poor camera resolution:** Keypoint detector confidence drops below threshold; noticed via real-time tracking error logs and UI visual hint "Insufficient lighting or hands not visible".
- **Camera hardware disconnect:** `cv2.VideoCapture` fails; caught gracefully with automatic reconnect backoff and clear user prompt.

## What I would change with more time
- Support continuous two-handed sentence parsing with an integrated language model (n-gram or small LLM) for grammatical sentence construction rather than isolated word tokens.
- Add WebRTC browser deployment for zero-install client access.
