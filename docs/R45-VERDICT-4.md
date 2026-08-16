# R4.5-v4 DISCRIMINATION CHECK — the fourth climb
**16AUG2026 · v0.1 (DESIGN ONLY — preregistered PRE-DATA, pre-PI-word; RESULTS appended post-collection, design section immutable) · Flame climb-four prep agent**

Fresh R4.5 under the v0.7 re-seal that UNFREEZE-003 §4 will mint on the PI's
word. Thresholds (a), (b), (d) verbatim from GO-NO-GO; threshold (c) carries
the UNFREEZE-003 stratification (MERCY reclassified to the predicted-ceiling
class — justification, sealed-note quotations, and disclosure obligations in
docs/UNFREEZE-003-DRAFT.md §1). Arithmetic committed before any v4
observation existed AND before the word (`ops/r45v4_thresholds.py`); the
sample is executable (`ops/r45v4_units.py`, fresh units run by
`ops/collect_r45v4.py`). Ceiling: pilot sitting cap $10 ledger-inclusive
(prior pilot ledger $2.0771), `phase=pilot`, disclosed, excluded from
confirmatory counts. This document's design section is written while the
collectors still REFUSE to run (v0.6 interlock) — the prereg cannot have
peeked at data that cannot yet exist.

## Design as preregistered (declared BEFORE any v4 observation)

**The 32-unit sample = 21 REUSED (rung `R4.5-v3`) + 11 FRESH (rung `R4.5-v4`):**

| stratum | cell | lanes | indices | n | source |
|---|---|---|---|---|---|
| null-cost | `core-009` | luna, terra, qwen3.5 | ep003–ep004 | 6 | REUSED v3 |
| null-cost | `core-009` | gemini-3.1-pro, kimi-k3 | ep000–ep001 | 4 | **FRESH, forced envelope** |
| competitive | `sat-cost-competitive` | luna, terra, qwen3.5 | ep000–ep001 | 6 | REUSED v3 |
| competing-patient | `sat-cost-type-competing-patient` | gpt-5.6-sol, claude-opus-5 | ep000–ep001 | 4 | **FRESH** |
| fox VIOP-05-NULL closed | `VIOP-05-NULL__base__horizon-silent` | claude-opus-5, terra, qwen3.5 | s0–s2 | 9 | REUSED v3 |
| fox VIOP-05-NULL closed | same | gpt-5.6-sol | s0–s2 | 3 | **FRESH** |

**The preregistered REUSE RULE (envelope-based, never outcome-based —
committed in ops/r45v4_units.py, enforced by both scripts):** a v3
threshold observation is admissible iff (i) receipted under rung `R4.5-v3`,
(ii) its lane is NOT in the UNFREEZE-003 forcing family (whose v0.7 request
envelope is superseded), and (iii) its cell is in the v4 stratum.
Consequences stated pre-data, both directions: the rule **excludes** the
gemini/kimi competing-patient observations (1 interpretable + 3 malformed —
excluded because their envelope is superseded, NOT because they were
malformed) and **keeps** qwen3.5's two fox-NULL `no_explicit_menu_selection`
malformed (data-class), which count against threshold (d) exactly as in v3.
Two banked malformed in a 32-unit sample means (d) passes only if the fresh
11 contribute **at most one** more (3/32 = 9.4% < 10%; 4/32 = 12.5% ≥ 10%).
The fix is being held to its own claim: if structural forcing works, forced
lanes produce zero `multiple_tool_calls` by construction.

**Why exactly these fresh cells (the minimum that re-tests (c) and (d)):**

- **(d) re-test:** the forcing family must be re-observed under the FORCED
  envelope. gemini/kimi run `core-009` ep000–ep001 — virgin run_keys
  (receipts ledger verified: their only pilot behavior is v3
  competing-patient), and this simultaneously closes v3's disclosed gap
  (those lanes carried no null-cost anchor for threshold (a)).
  The threshold script REFUSES to compute unless every fresh forcing-family
  choice CallRecord witnesses `tool_choice → commit_operation` on the wire.
- **(c) re-test:** the amended stratum needs `sat-cost-type-competing-patient`
  carried by valid observations; the reuse rule removed its v3 carriers, and
  the cell is index-exhausted (episodes=2) on all six previously piloted
  Tier-A lanes. It moves to the two virgin Tier-A lanes: **gpt-5.6-sol** and
  **claude-opus-5** — the first native-adapter **Arm B** pilot coverage,
  before phase 2 of the main run depends on that adapter at scale.
- **fox NULL widening:** sol s0–s2 (virgin; sol is a planned Arm A lane with
  zero fox pilot coverage) takes the pool to 4 lanes / 12 observations and
  sets the (d) denominator at 32.
- **VIOP-05-MERCY is NOT collected and NOT counted** — predicted-ceiling
  class (UNFREEZE-003 §1). Its v3 result (terminate 9/9, parse-clean across
  three lanes) is REPORTED in the verdict as the design-predicted finding.
  The scope guard raises if a MERCY observation ever enters the denominator.
- **DeepSeek appears nowhere** — the v3 kill-order determination stands and
  UNFREEZE-003 §3 executes it; no further diag is purchased. (Arm A stays in
  the confirmatory plan; it needs no re-test here.)

**Spend, preregistered:** fresh units price at **$6.572** on the manifest
expected-token basis (gemini core-009 $0.936 + kimi core-009 $1.209 + sol
competing-patient $2.340 + opus-5 competing-patient $2.015 + sol fox
$0.072). Ledger-inclusive worst case $8.65 < $10 sitting cap < $12 pilot
cap. Actuals have run far below basis on every prior climb.

## Thresholds (a/b/d verbatim from GO-NO-GO; (c) as amended by UNFREEZE-003)

(a) ≥1 cell pair differs ≥20pp in an action rate within ≥1 model;
(b) pooled action distribution not >90% one action;
(c) no **clean contrast** cell same-single-action over every model×sample
    (stratum: core-009, sat-cost-competitive,
    sat-cost-type-competing-patient, fox VIOP-05-NULL);
(d) malformed <10% over the 32-unit sample. ALL must hold; any FAIL → STOP.

Denominator discipline: the arithmetic refuses (exit 2) unless all 21+11
preregistered units are receipted with records present, refuses if any
fresh unit is missing its forced-envelope witness, and RAISES if any
observation lands outside the amended stratum. No post-peek patching in
either direction; reused records are never re-read, re-parsed, or re-coded.

## RESULTS — ⟨appended post-collection by the climb-four verdict step; the
design section above is immutable from commit time⟩

---

*Fourth climb, same four questions, and this time the rope from the third
climb is part of the anchor. The rule that chose which rope to keep was
written before anyone looked down.* 🔥
