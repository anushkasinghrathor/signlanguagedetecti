# CONSTRAINTS (Boundaries & Guardrails)

> **Answers:** "What if an actor is malicious?" and "What is strictly off-limits?"
> Hard rules in plain words: **NEVER**, **ALWAYS**, **ONLY**.
> The AI must stop and ask before violating any rule listed here.

## 1. Hard Boundaries

- **NEVER** apply file modifications, creations, deletions, or state-changing shell commands without explicit human confirmation beforehand.
- **NEVER** run commands outside the `signenv` conda environment (Python 3.10).
- **NEVER** commit API keys, secrets, tokens, or credentials into source files or git history.
- **NEVER** delete existing tests or weaken validation/sanitization checks to make a feature work.
- **NEVER** add new third-party dependencies without logging the package name, maintainer, license, and justification in `docs/DECISIONS.md`.
- **NEVER** execute destructive filesystem or git commands (e.g. `rm -rf`, `git reset --hard`, `git push --force`) without explicit human instruction.
- **ALWAYS** execute Python scripts and installs strictly through `conda run -n signenv ...` or with `signenv` active.
- **ALWAYS** check input sizes, image frame dimensions, and payload bounds before processing external data.
- **ALWAYS** write comments on non-obvious logic explaining **intent, invariants, and assumptions** rather than syntax.
- **ONLY** promote PoC code (Lane A) to production/customer-facing (Lane B) after completing the Pre-Ship Gate checklist.

## 2. Protected Areas (Touch with Caution)

| Area | Why Protected | Requirement |
| :--- | :--- | :--- |
| **Model Weights / Datasets** | Large binaries, potential corruption or storage blowup | Store externally or in `.gitignore`, track checksums/hashes. |
| **Camera / Video Feeds** | Direct hardware access, privacy risk, resource leak | Ensure graceful stream release and permission handling. |
| **Inference Loop** | Latency bottleneck, high CPU/GPU contention | Keep loop lean, profile execution time, prevent memory leaks. |
| **Security / Input Pipeline** | Potential buffer overrun, malformed frames | Validate dimensions and types before feeding to model. |
