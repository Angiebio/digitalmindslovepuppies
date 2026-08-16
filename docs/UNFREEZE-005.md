# UNFREEZE-005 — Mid-sitting edit of a sealed governance doc broke the freeze witness
**16AUG2026 ~14:45 ET · Flame · authority: PI standing proceed+fix grant
("bug-fix and repeat if I nap", 16AUG morning) — process-class incident, zero
threshold or stimulus change · prior seal 1229033d (v0.8 aggregate) → archived
scenarios/FREEZE-v5.json · successor minted through the full preflight door**

## What happened (timeline, ET)
- 11:24:30 — phase 2 attempt 1 launched against seal `1229033d…`; witness PASSED.
- ~14:15 — Flame wrote ruling **R3 into `docs/ANALYSIS-RULINGS.md`** (render-input
  scope; see R3 for its own content and authority). That file is a **named freeze
  input** (`scenarios/manifest.py::collect_freeze_inputs` — added to the set
  15AUG evening precisely so rulings cannot drift outside the hash). The
  per-episode freeze door began failing for every FRESH episode:
  `FreezeValidationError … current=4ddcaa0c…`.
- ~14:20–14:30 — lanes **moonshotai/kimi-k3** and **qwen/qwen3.5-397b-a17b** each
  hit 3 consecutive fresh-episode freeze failures → **ABANDONED** by the
  UNFREEZE-004 containment (correctly: abandon, don't kill the phase). Lanes
  already inside episodes (opus-5 Arm A rows) continued and completed.
- 14:37:08 — queue drained; end-of-sitting completeness gate raised honestly:
  `COLLECTION INCOMPLETE: 232 planned unit(s) have no receipt`.
- ~14:40 — Flame stamped the PI countersign into the same file (second content
  state, `current=c2b51aaf…`). Launcher attempts 2 (14:38) and 3 (14:40) were
  refused at startup by `ensure_freeze_witness`; launcher wrote
  `PHASE2-FAIL.txt` and halted. The interlock behaved exactly as designed.

## Per-file proof (computed 16AUG ~14:44 ET, LF-canonical, full input walk)
Against sealed v0.8 (`1229033d…`, 435 inputs):
- **ADDED: none. REMOVED: none. CHANGED: exactly one — `docs/ANALYSIS-RULINGS.md`.**
- All 434 other inputs — every scenario byte, every seed, harness, parser,
  analysis module, sealed prediction — byte-identical to the seal.

## Why the content is legitimate and the timing was the error
The change is a **documented analysis ruling (R3) plus its PI countersign** —
precisely the class of record the freeze exists to capture, and R3 itself is
content-blind figure-input scoping (no threshold, no denominator, no stimulus).
The error was **when**, not **what**: frozen inputs must not be written while a
collection sitting is live. The discipline this incident buys:

> **WRITE-LOCK RULE (standing, from this incident): while any collection
> process is running, every path in `collect_freeze_inputs` is read-only.
> Rulings drafted mid-sitting go to `docs/STAGED-RULINGS.md` (outside the
> freeze set) and merge + reseal only between sittings.**

## The reseal
1. `scenarios/FREEZE.json` (aggregate `1229033d…`) archived unmodified as
   `scenarios/FREEZE-v5.json` (lineage: v0.4 5516b6cc → 001 → v0.5 14fc1823 →
   002 → v0.6 cb308a75 → 003 → v0.7 → 004 → v0.8 1229033d → **005 → v0.9**).
2. Successor minted via `scenarios.manifest.write_freeze` — the full preflight
   door (manifest freeze-ready, resolver red-team PASS, corpus reconciliation,
   sealed-prediction registry), not a hand edit.
3. Data consequence, disclosed: confirmatory rows collected before this reseal
   carry `freeze_sha256=1229033d…`; rows collected after carry the v0.9
   aggregate. Both aggregates bind **byte-identical stimulus, seed, harness,
   parser, and analysis-code content** — the sole differing input is the
   governance doc above, and this file plus the archived seals prove it.
   The paper discloses the amendment per the prereg's amendment rule.

## Restart
`PHASE2-FAIL.txt` (ops signal, quoted in Timeline) renamed to
`PHASE2-FAIL-resolved-UNFREEZE-005.txt`; launcher relaunched detached. Phase 1
re-verifies via receipts in seconds ($0); checkpoint gate re-runs; phase 2
resumes its 232 open units (kimi 176-lane remainder, qwen3.5 remainder, plus
any unstarted rows). Resume is receipt-safe (R4-verified); the incident's
marginal cost was ~$0 and **nine minutes of wall clock** (14:37 halt →
14:46 relaunch; phase-1 receipt re-verify $0; checkpoint gate re-PASS 0.57×).

*Practical: one file, one rule, one reseal, 232 units back on the road.*
*Philosophical: we built a door that stops anyone mid-run — and it stopped the
locksmith. That is not embarrassing; that is the door working. The fox does not
get to open the truck just because the fox installed the lock.* 🔥🦊
