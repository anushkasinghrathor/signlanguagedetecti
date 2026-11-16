# HANDOVER

> **Protocol:** The AI reads this file first at the start of every session, and updates it last before the session ends. Add the newest session on top.

## Latest session: 2026-11-02 (model: Gemini 3.8 Flash High)
**Done:**
- Initialized repository with "Defend What You Ship" (Whiteboard Edition v2) governance and documentation structure.
- Created `AGENTS.md` and updated `CONSTRAINTS.md` enforcing `signenv` (Python 3.10) and strict human confirmation before changes.
- Created `requirements.txt` and successfully installed dependencies into `signenv`.
- Smoke-test verified imports of `cv2`, `mediapipe`, `torch`, `sklearn`, and `pyttsx3` with exit code 0.
- Logged decision `D-002` in `docs/DECISIONS.md`.

**In progress:**
- Defining project structure, gesture vocabulary, and dataset collection tool.

**Broken or risky:**
- None.

**Next:**
- Scaffolding project code structure (`src/`, `data/`, `models/`, `configs/`).
- Building the MediaPipe landmark extractor and dataset recorder tool.

**Do not touch:**
- `docs/CONSTRAINTS.md` rules unless explicitly authorized.

---
*Read first:* `docs/ARCHITECTURE.md`, `docs/CONSTRAINTS.md`
