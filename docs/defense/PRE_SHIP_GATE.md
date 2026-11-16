# THE PRE-SHIP GATE CHECKLIST

> **Rule:** Run this verification before anything in Lane B (Customer Facing) goes live.
> If you cannot tick every box honestly, **you are not ready to ship**.

- [ ] **1. High-Level Mental Model:** I can explain how this works at a high level, without notes.
- [ ] **2. Current Defense Brief:** `docs/defense/DEFENSE.md` is written in human words and is up to date.
- [ ] **3. Defensible Alternatives:** I know why we chose this approach over at least one real alternative.
- [ ] **4. Threat Defense:** I can name who could abuse this system and what controls stop them.
- [ ] **5. Known Failure Boundary:** I know the first place this will fail and how we would detect it.
- [ ] **6. Data Structure Rationale:** I know the main data structures used and why they suit the access patterns.
- [ ] **7. Full Diff Reviewed:** I inspected the actual code diff line-by-line, not just the AI's generated summary.
- [ ] **8. Real Test Output Verified:** Automated tests ran and actual console pass output was inspected (no vibe checks).
- [ ] **9. End-to-End Customer Path Tested:** A customer path was manually executed by hand end to end.
- [ ] **10. Zero Secrets in Code:** No API keys, credentials, tokens, or `.env` files are tracked in source code.
- [ ] **11. Dependencies Justified:** All new libraries/dependencies are recorded, justified, and audited in `docs/DECISIONS.md`.
- [ ] **12. Rollback Ready:** Rollback steps are verified in `docs/ROLLBACK.md` and the last known good commit is noted.
- [ ] **13. Assumptions Cleared:** All unverified AI assumptions have been resolved or consciously accepted.
- [ ] **14. Living Docs Updated:** `docs/HANDOVER.md` and `docs/DECISIONS.md` have been updated with the latest session state.
