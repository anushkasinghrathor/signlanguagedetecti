# ROLLBACK (Safety Net & Reversal Procedures)

> **Answers:** "Where does this fail?" and "How do you undo your last change safely?"
> Confidence to let AI make bigger changes comes from knowing exactly how to reverse them.

---

## 1. Fast Rollback Procedure

In the event of a breaking regression or unhandled exception in Lane B:

1. **Check Last Known Good Commit:**
   ```bash
   git log --oneline -n 5
   ```
2. **Revert the Problematic Commit:**
   ```bash
   git revert <commit-hash> --no-edit
   ```
   *(Or for local working changes: `git restore .`)*
3. **Verify Clean Working Tree:**
   ```bash
   git status
   ```
4. **Run Smoke Test:**
   ```bash
   pytest tests/smoke/ -v
   ```

---

## 2. Model & Weight Rollbacks

- Model files and weights are versioned under tags or release assets (e.g. `weights/model_v1.0.onnx`).
- If an updated model version exhibits accuracy degradation or latency spikes:
  1. Update config file `configs/model_config.yaml` to point back to previous model checkpoint:
     ```yaml
     model_path: "weights/model_v1.0.onnx"
     ```
  2. Restart application or reload inference session.

---

## 3. Log of Rollback Anchors

| Date | Last Known Good Commit | Author / Model | Notes |
| :--- | :--- | :--- | :--- |
| 2026-11-02 | Initial Repo Scaffold | Gemini 3.8 Flash High | Baseline framework initialization |
