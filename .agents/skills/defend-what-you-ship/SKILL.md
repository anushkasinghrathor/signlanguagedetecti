---
name: defend-what-you-ship
description: >-
  Use this skill to implement, audit, and enforce the "Defend What You Ship" (Whiteboard Edition v2)
  methodology. Covers the 25 AI collaboration habits, running Pre-Ship Gate audits, conducting
  Whiteboard Defense drills, drafting decision records, and managing session handover files.
---

# Defend What You Ship — Skill & Runbook

This skill operationalizes the **"Defend What You Ship" (Whiteboard Edition v2)** field guide for building with AI.

## When to Use This Skill
- **Session Kickoff:** Read [docs/HANDOVER.md](../../../docs/HANDOVER.md) to resume context without amnesia.
- **Before Architecture/Code Changes:** Draft [docs/DECISIONS.md](../../../docs/DECISIONS.md) and verify [docs/CONSTRAINTS.md](../../../docs/CONSTRAINTS.md).
- **Session Wrap-up:** Append a 5-line handoff note and quiz for unverified assumptions.
- **Before Customer Release (Lane B):** Run the Pre-Ship Gate checklist and conduct a Whiteboard Drill.
- **New Project Scaffolding:** Run the `init-defend.ps1` helper script to initialize any project in seconds.

---

## The 4 Whiteboard Defense Questions
Be prepared to answer these four questions at any time:
1. **"Why did you do X instead of Y?"**
   - Red flag: *"The AI suggested it."*
   - Defense: Cite options considered, relative costs, and specific winning factors in [docs/DECISIONS.md](../../../docs/DECISIONS.md) & [docs/ALTERNATIVES.md](../../../docs/ALTERNATIVES.md).
2. **"What happens if this actor behaves maliciously?"**
   - Red flag: *"Users wouldn't do that."*
   - Defense: Specify actors, trust boundaries, rate limits, and mitigations in [docs/THREAT.md](../../../docs/THREAT.md).
3. **"What data structure did you use here and why?"**
   - Red flag: *Not knowing the structure exists or why it fits the access pattern.*
   - Defense: State shape, access pattern, size bounds, and trade-offs in [docs/DATA.md](../../../docs/DATA.md).
4. **"Where does this fail?"**
   - Red flag: *"It should not fail."*
   - Defense: Walk dependency failure modes, rate limits, timeouts, and alerting in [docs/FAILURE.md](../../../docs/FAILURE.md).

---

## Workflows & Commands

### 1. Initialize Defend Structure in a New Repo
Run the initialization PowerShell script:
```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/defend-what-you-ship/scripts/init-defend.ps1 -TargetDir "C:\path\to\new\project"
```

### 2. Conducting the Whiteboard Drill (Self-Test)
When the user requests `/grill-me` or asks to practice whiteboard defense:
1. Review the current code and `docs/defense/DEFENSE.md`.
2. Ask the user the 12 questions from [docs/defense/WHITEBOARD_DRILL.md](../../../docs/defense/WHITEBOARD_DRILL.md) one by one.
3. Grade their answers constructively:
   - Identify weak spots, unverified assumptions, or missing trade-offs.
   - Update `docs/` to plug any discovered gaps.

### 3. Pre-Ship Gate Audit
Before promoting code from Lane A (PoC) to Lane B (Customer Facing):
1. Walk through all 14 items in [docs/defense/PRE_SHIP_GATE.md](../../../docs/defense/PRE_SHIP_GATE.md).
2. Confirm test executions with real paste output.
3. Confirm absence of hardcoded secrets or arbitrary dependencies.
