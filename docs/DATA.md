# DATA (Structures, Schemas & Trade-offs)

> **Answers:** "What data structure did you use here and why?"
> The AI picked one. You need to know why it was a good pick.
> Record shape, access patterns, expected size, trade-offs, and read/write ownership.

---

## 1. Core Data Structures

### A. Temporal Frame Buffer (`collections.deque`)
- **Shape / Type:** `deque(maxlen=30)` containing numpy arrays of shape `(21, 3)` (21 3D hand landmarks).
- **Access Pattern:** Append-only on right (`append()`) at 30 FPS; read as fixed-size contiguous numpy array for inference.
- **Expected Size:** 30 frames × 63 floats ≈ 7.5 KB in RAM (negligible memory footprint).
- **Trade-off:**
  - *Pro:* O(1) push and auto-eviction of oldest frame without expensive array copying.
  - *Con:* Requires converting to a contiguous NumPy array slice before feeding to PyTorch/ONNX.
- **Ownership:** Written only by `pipeline/buffer.py`; read only by `models/inference.py`.

### B. Landmark Keypoint Vector (`np.ndarray`)
- **Shape / Type:** Float32 array of shape `(63,)` (21 coordinates × [x, y, z] normalized relative to wrist).
- **Access Pattern:** Computed once per frame, read sequentially by normalizer and buffer.
- **Expected Size:** 252 bytes per detected hand.
- **Trade-off:**
  - *Pro:* Extremely fast vector operations and spatial transformations using vectorized NumPy SIMD.
  - *Con:* Fixed dimension; missing joints must be imputed or zero-padded if a landmark detector drops a point.
- **Ownership:** Written only by `pipeline/preprocessor.py`; read by buffer.

### C. Gesture Class Label Map (`dict` / `list`)
- **Shape / Type:** Index-to-label array: `["Hello", "Thank You", "Yes", "No", ...]` of length `C`.
- **Access Pattern:** Constant time O(1) integer indexing by predicted argmax.
- **Expected Size:** ~100 to 500 strings.
- **Trade-off:**
  - *Pro:* O(1) lookup speed, minimal overhead.
  - *Con:* Rigid ordering; adding classes requires matching model output heads.
- **Ownership:** Read-only constant loaded from config on startup.
