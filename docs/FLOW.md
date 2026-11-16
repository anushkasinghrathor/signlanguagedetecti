# FLOW (Traceability & Call Paths)

> **Answers:** "Where does this fail?" and "How does execution actually travel?"
> Trace from entry point to output: file -> function -> next file -> next function.
> Update whenever an execution path changes.

## 1. Primary Execution Flow

```text
[Entry Point: main.py / app.py]
  │
  ├── 1. init_camera() -> cv2.VideoCapture(0)
  │       └── Returns: stream handle or error
  │
  ├── 2. capture_loop() [Loop running while camera active]
  │       │
  │       ├── read_frame()
  │       │     └── Check: frame is not None, valid shape (H, W, C)
  │       │
  │       ├── pipeline/preprocessor.py: extract_landmarks(frame)
  │       │     └── MediaPipe Hands / Holistic
  │       │     └── Returns: Normalized landmark vector [x1, y1, z1, ...]
  │       │
  │       ├── pipeline/buffer.py: update_sliding_window(landmarks)
  │       │     └── Buffer shape: (sequence_length, feature_dim)
  │       │
  │       ├── models/inference.py: predict(sequence)
  │       │     └── Model forward pass
  │       │     └── Returns: probabilities / top-k classes
  │       │
  │       ├── pipeline/postprocessor.py: smooth_prediction(probabilities)
  │       │     └── Debounce / threshold filter (e.g. confidence > 0.85)
  │       │
  │       └── ui/display.py: render_overlay(frame, text, confidence)
  │             └── Returns: output display frame / event
  │
  └── 3. cleanup() -> release camera, close windows, free GPU memory
```

## 2. Gaps & Potential Drop-offs

| Boundary | What travels across | Potential failure point |
| :--- | :--- | :--- |
| Camera -> Preprocessor | Raw numpy array / BGR frame | Dropped camera connection, corrupted byte buffer |
| Preprocessor -> Buffer | Landmark array (float coordinates) | No hands detected in frame (empty array) |
| Buffer -> Model | Fixed-size tensor window | Incomplete window buffer on initial startup |
| Model -> UI | Class index & confidence score | Below threshold / false positive flicker |
