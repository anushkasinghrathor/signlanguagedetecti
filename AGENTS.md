# DEFEND WHAT YOU SHIP — AGENT INSTRUCTIONS

This project adheres to the **"Defend What You Ship (Whiteboard Edition v2)"** methodology.
Every prompt, code generation, and change must be defensible. The human developer is the director and author of decisions; the AI assists with rigor, transparency, and traceability.

---

## 1. The Two Lanes (Operating Mode)

Before starting work, determine which lane this project/task is in:
* **Lane A (PoC / Demo / Experiment):**
  - Goal: Learn fast, test an idea, disposable.
  - Speed over quality. Minimal documentation required.
  - *Promotion Rule:* The moment real users or production data touch this code, it **immediately moves to Lane B**.
* **Lane B (Customer Facing / Production):**
  - Goal: Reliability, safety, clarity, correctness.
  - Defensible at a whiteboard without notes.
  - All rules below are **STRICTLY ENFORCED**.

---

## 2. Session Protocol (Start & End)

1. **Session Start — Read First:**
   - Always read [docs/HANDOVER.md](file:///c:/Study/signlanguagedetection/docs/HANDOVER.md) first to understand the current state.
   - Check [docs/CONSTRAINTS.md](file:///c:/Study/signlanguagedetection/docs/CONSTRAINTS.md) for hard boundaries (never/always/only).
   - Check [docs/ARCHITECTURE.md](file:///c:/Study/signlanguagedetection/docs/ARCHITECTURE.md) to understand trust boundaries and system maps.

2. **Session End — Update Last:**
   - Conclude every session with a 5-line handoff summary in [docs/HANDOVER.md](file:///c:/Study/signlanguagedetection/docs/HANDOVER.md):
     1. What was done
     2. What is in progress
     3. What is broken or risky
     4. What is next
     5. Do not touch / watch out for
   - Prompt the user with **Assumption Check**: *"Here is what I assumed during this task that you didn't explicitly specify: [list]. Are any of these incorrect or unverified?"*

---

## 3. The 4 Whiteboard Defense Questions

Every Lane B system change must be prepared to answer:
1. **"Why did you do X instead of Y?"**
   - Provide alternatives considered, their relative costs/trade-offs, and why this chosen approach won.
   - *Red Flag:* "The AI suggested it." (AI is a source, not a reason). Back up with [docs/DECISIONS.md](file:///c:/Study/signlanguagedetection/docs/DECISIONS.md) and [docs/ALTERNATIVES.md](file:///c:/Study/signlanguagedetection/docs/ALTERNATIVES.md).
2. **"What happens if this actor behaves maliciously?"**
   - Name actors (anonymous, logged-in, malicious insider, poisoned dependency). Detail validation, auth checks, rate limits, and least privilege.
   - *Red Flag:* "Users wouldn't do that." Back up with [docs/THREAT.md](file:///c:/Study/signlanguagedetection/docs/THREAT.md).
3. **"What data structure did you use here and why?"**
   - State data shape, access patterns (read vs. write heavy), size bounds, and trade-offs (e.g. fast lookup vs costly ordering). Back up with [docs/DATA.md](file:///c:/Study/signlanguagedetection/docs/DATA.md).
4. **"Where does this fail?"**
   - Name the first limit (traffic, concurrency, timeouts), failure modes of dependencies, and how we detect it (logs, alerts).
   - *Red Flag:* "It should not fail." Back up with [docs/FAILURE.md](file:///c:/Study/signlanguagedetection/docs/FAILURE.md) and [docs/TESTING.md](file:///c:/Study/signlanguagedetection/docs/TESTING.md).

---

## 4. Coding & Workflow Habits

* **Strict Confirmation Protocol (MANDATORY):**
  - **NEVER** modify, create, or delete files, nor run modifying shell commands, without first presenting the plan, affected files, proposed diff, and risks to the user.
  - Wait for explicit user confirmation before touching any file.
* **Environment Discipline (`signenv`):**
  - All Python scripts, tests, dependencies, and execution commands must run strictly inside the `signenv` conda environment (`conda run -n signenv ...`).
* **Habit 11: Ask Why Before What (Plan First):**
  - Before editing code for any non-trivial change, explain the plan, alternatives, and potential failure modes.
  - Obtain approval on the plan before touching code.
* **Habit 2: Draft DECISIONS.md Before the Change:**
  - For any architectural choice, pattern, or library, draft the entry in [docs/DECISIONS.md](file:///c:/Study/signlanguagedetection/docs/DECISIONS.md) before implementing it.
  - Pin the active AI model name and version, date, context, options, choice, why, trade-off, and "revisit if" condition.
* **Habit 3: Explicit Comments:**
  - Write comments explaining intent and flow, not repeating syntax.
  - Mark invariants (e.g., `# INVARIANT: must run after auth check`).
  - Add `# WHY:` notes for surprising or non-obvious workarounds so they aren't inadvertently cleaned up.
* **Habit 10: Review Diffs & Red Flags:**
  - Never delete or loosen tests or validation checks without explicit discussion.
  - Flag any unexpected file touch, hardcoded secrets, or new network calls.
* **Habit 12 & 23: Small Scoped Changes & Intent-Driven Commits:**
  - One logical change per step.
  - Commit message format: Explain *what* changed and *why*, not just generic summaries.
* **Habit 22: Least Privilege Allow Policy:**
  - Safe to auto-run: Read files, list folders, run tests/linters, format code.
  - Pause and confirm: Edits across many files, dependency changes, schema/db writes, new network hosts, file deletions.
  - Never allow blindly: Secrets/.env edits, production deployments, force pushes, disabling tests or security checks.
* **Habit 24: Dependency & Secrets Hygiene:**
  - Never introduce a new package without documenting why it is needed and who maintains it.
  - Never place credentials, keys, or tokens in source code.

---

## 5. Pre-Ship Gate (Lane B)

Before declaring any feature or system ready for production / customer use, verify all 14 criteria in [docs/defense/PRE_SHIP_GATE.md](file:///c:/Study/signlanguagedetection/docs/defense/PRE_SHIP_GATE.md).
If the developer cannot answer the Whiteboard Drill questions confidently without notes, the code is **not ready to ship**.
