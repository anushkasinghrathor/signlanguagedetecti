# TESTING (Verification Checklist & Real Outputs)

> **Answers:** "Where does this fail?" and "How do we prove it works?"
> An AI claiming success and code actually working are two different facts.
> Always run actual commands and inspect real terminal output. No vibe checks.

---

## 1. Automated Test Suite

| Test Suite | Command | What a PASS looks like |
| :--- | :--- | :--- |
| **Lint & Syntax** | `flake8 src/` or `ruff check .` | Exit code 0, no errors reported. |
| **Unit Tests** | `pytest tests/unit/ -v` | All tests marked `PASSED`, 0 failures. |
| **Pipeline Integration** | `pytest tests/integration/ -v` | Real synthetic video frames flow through preprocessor and model without exceptions. |
| **Benchmark / FPS** | `python scripts/benchmark_fps.py` | Average FPS >= 30, max frame processing latency <= 33ms. |

---

## 2. Real Output Verification Rule

Whenever running tests, the AI must never simply claim *"all tests passed"*.
The actual console output and exit code must be recorded:
```bash
# Example required output verification:
# ============================== 12 passed in 1.42s ==============================
```

---

## 3. End-to-End Customer Path (Manual Verification)

*Before shipping any customer-facing release, execute this manual path:*
1. Launch the application via `python src/main.py`.
2. Confirm the webcam initialization prompt appears and grants access within 2 seconds.
3. Hold up a hand performing the "Hello" gesture in front of the lens.
4. Verify the UI overlays the text "Hello" with confidence >= 85%.
5. Move hand out of frame; verify the prediction transitions cleanly to "Idle" without freezing or throwing index errors.
6. Press `q` to terminate; verify camera device is cleanly released and terminal returns with exit code 0.
