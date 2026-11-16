# FAILURE (Resilience & Failure Modes)

> **Answers:** "Where does this fail?"
> "Where does this fail is the question that separates people who understand a system from people who merely deployed it."
> Walk each dependency: What if it is slow, down, wrong, or empty?

---

## 1. Dependency Failure Matrix

| Dependency | If Down / Unreachable | If Slow / High Latency | If Wrong / Corrupt Output | If Empty / Zero-length |
| :--- | :--- | :--- | :--- | :--- |
| **Camera Hardware** | `cv2.VideoCapture` fails to open; return friendly error message & retry prompt. | Frame queue lags behind real-time; skip lagging frames to keep sync. | Corrupted pixels/green screen; frame validation rejects frame. | 0 bytes read (`ret == False`); gracefully restart capture loop. |
| **MediaPipe / Landmark Extractor** | Fallback to previous frame landmarks or return `NoHandsDetected`. | FPS drops below threshold; downsample input resolution dynamically. | Erroneous keypoints (hand occluded); confidence score drops, output suppressed. | Hand outside frame; buffer retains idle state, prevents bogus predictions. |
| **Model Inference Engine** | Crash if CUDA OOM; auto-fallback to CPU inference mode. | High inference latency; drop to smaller sequence window or quantization. | Nonsensical label predicted; probability threshold filter rejects output. | Model returns NaN or empty logits; catch exception, log warning, skip emit. |
| **Output / Audio TTS Service** | Text still renders to screen; audio muted silently with UI warning indicator. | Audio playback delays behind gesture; queue audio with debounce. | Distorted audio synthesis; fallback to screen display only. | Empty translation text; do not trigger audio output. |

---

## 2. Limits & Thresholds

- **First Limit Expected to Hit:** GPU/CPU saturation if processing high frame-rate video without dropping old frames in the buffer.
- **Max Input Dimensions:** 1280x720 (higher resolutions are automatically downsampled to 640x480).
- **Temporal Window Bound:** Sliding window maximum size: 30 frames (~1 second of gesture).
- **Latency Budget:** Total pipeline latency must stay under 40ms per frame to maintain >= 25 FPS real-time feedback.

---

## 3. Observability: How We Find Out

- **Console / Log Metrics:** Real-time FPS counter, dropped-frame count, and inference duration logged every 100 frames.
- **Alert Conditions:**
  - If FPS < 15 for more than 3 consecutive seconds: Log `WARNING: Pipeline bottleneck detected`.
  - If camera read fails 5 times consecutively: Raise `CameraDisconnectedError`.
