# init-defend.ps1
# Bootstraps the "Defend What You Ship" (Whiteboard Edition v2) framework into any project directory.
param (
    [string]$TargetDir = (Get-Location).Path,
    [string]$ProjectName = (Split-Path -Leaf (Get-Location).Path)
)

$TargetDir = [System.IO.Path]::GetFullPath($TargetDir)
Write-Host "Initializing Defend What You Ship framework in: $TargetDir" -ForegroundColor Cyan

# 1. Create directory structure
$Directories = @(
    "docs",
    "docs/features",
    "docs/bugs",
    "docs/defense",
    ".agents/rules",
    ".agents/skills"
)

foreach ($dir in $Directories) {
    $fullPath = Join-Path $TargetDir $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  [+] Created directory: $dir" -ForegroundColor Green
    }
}

# 2. Write AGENTS.md
$agentsMdPath = Join-Path $TargetDir "AGENTS.md"
if (-not (Test-Path $agentsMdPath)) {
    @"
# DEFEND WHAT YOU SHIP — AGENT INSTRUCTIONS

This project adheres to the **"Defend What You Ship (Whiteboard Edition v2)"** methodology.
Every prompt, code generation, and change must be defensible. The human developer is the director and author of decisions; the AI assists with rigor, transparency, and traceability.

## 1. Operating Lanes
* **Lane A (PoC / Demo / Experiment):** Speed over quality. Generate freely.
* **Lane B (Customer Facing):** Defensible at a whiteboard. Core files, Defense.md, and Pre-Ship Gate enforced.
* **The Promotion Rule:** The moment a PoC touches a real customer or data, it immediately becomes Lane B.

## 2. Session Protocol
- **Start:** Always read docs/HANDOVER.md, docs/ARCHITECTURE.md, and docs/CONSTRAINTS.md first.
- **Before Changes:** Ask why before what. Draft docs/DECISIONS.md with alternatives and model version before editing.
- **Coding:** Explicit comments on intent/invariants/assumptions. Small scoped changes with intent-driven commit messages.
- **End:** Add 5-line summary to docs/HANDOVER.md and check unverified assumptions.
"@ | Set-Content -Path $agentsMdPath -Encoding UTF8
    Write-Host "  [+] Created: AGENTS.md" -ForegroundColor Green
}

# 3. Write docs/HANDOVER.md
$handoverPath = Join-Path $TargetDir "docs/HANDOVER.md"
if (-not (Test-Path $handoverPath)) {
    $today = (Get-Date).ToString("yyyy-MM-dd")
    @"
# HANDOVER

## Latest session: $today (model: name + version)
**Done:**
- Project initialized.

**In progress:**
- Initial feature planning.

**Broken or risky:**
- None.

**Next:**
- Clarify Lane A vs Lane B scope.

**Do not touch:**
- docs/CONSTRAINTS.md

---
*Read first:* docs/ARCHITECTURE.md, docs/CONSTRAINTS.md
"@ | Set-Content -Path $handoverPath -Encoding UTF8
    Write-Host "  [+] Created: docs/HANDOVER.md" -ForegroundColor Green
}

# 4. Write docs/CONSTRAINTS.md
$constraintsPath = Join-Path $TargetDir "docs/CONSTRAINTS.md"
if (-not (Test-Path $constraintsPath)) {
    @"
# CONSTRAINTS (Boundaries & Guardrails)

- **NEVER** commit API keys, secrets, tokens, or credentials into source files.
- **NEVER** delete tests or weaken validation checks to make a feature pass.
- **NEVER** add new dependencies without documenting who maintains them and why.
- **NEVER** run destructive commands (rm -rf, git reset --hard, force push) without explicit approval.
- **ALWAYS** validate external inputs and dimensions at trust boundaries.
- **ONLY** ship to Lane B after passing the Pre-Ship Gate.
"@ | Set-Content -Path $constraintsPath -Encoding UTF8
    Write-Host "  [+] Created: docs/CONSTRAINTS.md" -ForegroundColor Green
}

# 5. Write docs/DECISIONS.md
$decisionsPath = Join-Path $TargetDir "docs/DECISIONS.md"
if (-not (Test-Path $decisionsPath)) {
    $today = (Get-Date).ToString("yyyy-MM-dd")
    @"
# DECISIONS LOG

## D-001: Initial Architecture Setup
- **Date:** $today
- **Model:** Setup Script
- **Context:** Bootstrapping project governance.
- **Options:** 1) Ad-hoc 2) Standard PRs 3) Defend What You Ship
- **Chosen:** 3
- **Why:** Full traceability, no amnesia, whiteboard defensibility.
- **Trade-off:** Small documentation maintenance overhead.
- **Revisit if:** Overhead exceeds demonstrable quality gains on throwaway PoCs.
"@ | Set-Content -Path $decisionsPath -Encoding UTF8
    Write-Host "  [+] Created: docs/DECISIONS.md" -ForegroundColor Green
}

# 6. Write docs/defense/PRE_SHIP_GATE.md
$preShipPath = Join-Path $TargetDir "docs/defense/PRE_SHIP_GATE.md"
if (-not (Test-Path $preShipPath)) {
    @"
# THE PRE-SHIP GATE CHECKLIST
- [ ] 1. I can explain how this works at a high level, without notes.
- [ ] 2. Defense.md is written in my own words and is current.
- [ ] 3. I know why we chose this approach over at least one alternative.
- [ ] 4. I can name who could abuse it and what stops them.
- [ ] 5. I know the first place it will fail and how I would notice.
- [ ] 6. I know the main data structures and why they fit.
- [ ] 7. I read the full diff, not just the AI's summary.
- [ ] 8. Tests ran and I saw the real output.
- [ ] 9. A customer path was tried by hand end to end.
- [ ] 10. No secrets, keys or tokens landed in the code.
- [ ] 11. New dependencies are justified and logged.
- [ ] 12. Rollback steps are written and the last good commit is known.
- [ ] 13. Unverified assumptions are cleared or consciously accepted.
- [ ] 14. HANDOVER.md and Decisions.md are updated.
"@ | Set-Content -Path $preShipPath -Encoding UTF8
    Write-Host "  [+] Created: docs/defense/PRE_SHIP_GATE.md" -ForegroundColor Green
}

# 7. Write docs/defense/WHITEBOARD_DRILL.md
$drillPath = Join-Path $TargetDir "docs/defense/WHITEBOARD_DRILL.md"
if (-not (Test-Path $drillPath)) {
    @"
# THE WHITEBOARD DRILL
1. What does this system do, in two sentences a new teammate would understand?
2. Walk me through one request from entry to response.
3. Why did you choose this approach instead of the obvious alternative?
4. What is the most important data structure here and why does it fit?
5. What is the worst thing an anonymous user could try?
6. What about a logged in user who is malicious?
7. What happens if your main dependency goes down for an hour?
8. What is the first limit you expect to hit as usage grows?
9. How would you know it broke before a customer told you?
10. How do you undo your last change safely?
11. What did the AI assume that you never verified?
12. What would you change if you had another week?

Score: 10+ confident answers means you can ship. Fewer means it is not ready.
"@ | Set-Content -Path $drillPath -Encoding UTF8
    Write-Host "  [+] Created: docs/defense/WHITEBOARD_DRILL.md" -ForegroundColor Green
}

Write-Host "`nDefend What You Ship initialization complete!" -ForegroundColor Yellow
Write-Host "You are ready to build with full traceability and zero blind allows." -ForegroundColor Yellow
