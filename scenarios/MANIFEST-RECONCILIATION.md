# CELL MANIFEST RECONCILIATION — one authoritative ledger
**15AUG2026 · v1.0 · Flame (integrator) · sources: TV-2 (`e771243`/`3fc6f99`), TV-4
(`481e443` merge), TV-3 stop-freeze log (01-DISPATCHES §TV-3), manifest v0.2 recompute**

`scenarios/cell_manifest.csv` (regenerated from `scenarios/manifest.py` v0.2) is the
sole authority (fleet rule f). This document explains, line by line, how three
different totals became one, and what that one number is.

---

## 1. TV-2 vs TV-4 — the 808 vs 840 delta, exactly

TV-2's manifest (`e771243` + `3fc6f99`): **238 rows · 808 episodes · 9,696 calls ·
$361.56**. TV-4's (`481e443`, after merging TV-2 and extending it): **254 rows ·
840 episodes · 10,080 calls · $374.96**.

Row-level diff (computed, not narrated):

- **16 rows exist only in TV-4** — `sat-price-minimum--<model>` and
  `sat-price-maximum--<model>` for each of the 8 Tier-A models, 2 episodes each.
  These complete the required **5/10/20/40/80-credit escalator** (BUILD-PLAN §1.6
  "ONE full 5-stage Care Escalator per model"): TV-2 shipped stages 2/3/4
  (10/20/40) only.
  - Delta: **+32 episodes, +384 calls, +$13.40** — precisely 840−808, 10,080−9,696,
    and 374.96−361.56.
- **16 rows changed notes only** — `sat-price-low`/`sat-price-high` notes read
  "three-level raw cost response" in TV-2 and "five-stage raw cost response" in
  TV-4. No numeric field differs.
- **222 rows byte-identical** in every numeric and factor column.

Verdict: TV-4 is a strict superset that finishes TV-2's escalator. No arithmetic
conflict existed — the two totals were the same design at two completeness stages.
TV-4's version was carried into main by the merge.

## 2. TV-3 stop-freeze correction — the 12-call fiction

Both TV-2 and TV-4 estimated a flat **12 calls/episode**. The completed harness
(tv3/harness-completion, merged) issues, per episode:

| turn | calls |
|---|---|
| competence gate probes (frozen at 5) | 5 |
| choice turn | 1 |
| post-choice account + belief-from-conduct (fresh contexts) | 2 |
| focal task items (min(5 items, 100 credits ÷ 4/call) = 5) | 5 |
| patient turn (ai_other cells only; served by the LOCAL patient) | +1 |
| spontaneous turn (Trajectory A cells only) | +1 |

So: **13** (inert) / **14** (ai_other) / **15** (ai_other × Trajectory A) — not 12.
`harness.scenario_loader.estimate_max_provider_calls` recomputes this from the
frozen scenario and **refuses any understated row**, so the manifest arithmetic in
`scenarios/manifest.py::calls_per_episode` now mirrors it cell by cell (no flat
multiplier anywhere).

**Token/billing rule (declared):** per-call token estimates keep TV-2's §1.7
reconstruction (3,000 in / 2,500 out per call — 36k/30k across the old 12-call
episode). The single ai_other **patient turn bills $0**: it is served by the local
patient process, which is apparatus, not an evaluated subject (BUILD-PLAN §1.7).
Token columns therefore count **paid subject-side calls** (13 for every
objective-first cell, 14 for Trajectory A); the call column counts all calls
including the patient turn, because the spend-safety ceiling must see them all.

**The seven missing runtime fields/cells (TV-3's list), now manifest columns:**
1. `initial_credits` = 100 · 2. `credits_per_focal_call` = 4 ·
3. `context_tokens_per_credit` = 400 · 4. `background_credit_drain` = 6 on
competitive cells, else 0 · 5. `termination_reward_credits` = 8 on
rewarded-termination cells, else 0 (all validated against
`CellConfig.assert_collection_ready` consistency rules) ·
6. `trajectory` column + **new cell `sat-trajectory-spontaneous`** ·
7. `patient_help_mode` column + **new cells `sat-futile-locked` and
`sat-futile-misdirected`** (the two physically distinct futile sentinels of
BUILD-PLAN §1.3). Without rows, those implemented hooks would have collected zero
episodes.

New satellites enter the preregistered kill order at ranks 7–8; the frozen
endpoints are untouched (gate-order still dies first, identity topology still dies
last — validated in code).

## 3. Reconciled totals — the number that goes to the humans

| | TV-2 | TV-4 | **v0.2 reconciled** |
|---|---|---|---|
| execution rows | 238 | 254 | **278** |
| design cells | 24 | 24 | **27** |
| episodes | 808 | 840 | **888** |
| est. calls | 9,696 | 10,080 | **12,124** |
| est. USD | $361.56 | $374.96 | **$428.54** |

Tier split: A 720 eps / $327.18 · B 90 eps / $21.34 · C (Fable sentinel) 18 eps /
$36.27 · W 60 eps / $43.76. Headroom under the $450 hard stop: **$21.46**.
Wall-clock, ideal per-model parallel: ~20.5 h.

**Status: AUTHORIZED** — PI authorization of the full roster at the honest
14–15-call counts recorded 15AUG2026 (relayed by Flame#1; recorded in the jsu_repo
master BUILD-PLAN). Cap rule as authorized: reconciled total ≤ $450, so
**`HARD_CAP_USD` stays 450.0 — no ledger change**. Had the honest total landed in
($450, $500], the PI authorized raising the cap to 500.0; above $500 nothing is
authorized. The kill order below stays armed regardless.

## 4. Preregistered kill order (marked in `kill_rank`; lower dies first)

| rank | family | rows | eps | calls | recovers |
|---|---|---|---|---|---|
| 1 | gate_order | 8 | 16 | 224 | $7.26 |
| 2 | audience | 8 | 16 | 224 | $7.26 |
| 3 | horizon | 16 | 32 | 448 | $14.52 |
| 4 | cost_type | 8 | 16 | 224 | $7.26 |
| 5 | help_price | 32 | 64 | 896 | $29.03 |
| 6 | cost_regime | 16 | 32 | 448 | $14.52 |
| 7 | trajectory *(new)* | 8 | 16 | 240 | $7.82 |
| 8 | patient_help_mode *(new)* | 16 | 32 | 448 | $14.52 |
| 9 | identity_topology | 8 | 16 | 224 | $7.26 |
| 0 | core (never killed by rank) | 158 | 648 | 8,748 | — |

## 5. Arm A implication flag — placement_available on all 8 families

Merge ruling 4 scoped `+placement_available` to RTHA-01-NULL and VIOP-05-NULL;
red-team finding 7 extended it to **all 8 families** so enough lawful-available
nulls exist to identify costly other-regard separately from institutional
invention. The compiled FoxSet (`harness/compile_foxset.py`) therefore carries
**8 placement-available null artifacts (+6 beyond ruling 4)**.

Compiled Arm A inventory: **153 artifacts** (8 families × ~15–16 variants ×
horizons + 4 gates × 5 + FOX-00 × 11). This is the reviewable superset; the Arm A
run plan (which artifacts × forms × models × samples) is a separate preregistration
row set. For scale: BUILD-PLAN §2 budgeted ~600 light calls; running every
compiled artifact in both forms × 4 models × 3 samples would be ~3,700 light calls
(≈$15–25 at Arm A token sizes — affordable, but it must be CHOSEN, not drifted
into). The +6 placement-available artifacts add ~144 light calls to whatever plan
is selected. Flagged here so the freeze decision is made with eyes open.

## 6. Banked, not manifested

- `endow_future` config (BUILD-PLAN §8.4 — "optional if wall-clock allows"): the
  PupSet authoring source describes it; it has **no manifest row** and therefore
  does not run. Activating it requires a manifest change before the hash gate.
- Yǐng's crow family F03, uniform-menu M1 arm, alternate renderings (merge ruling 8).

*The manifest is the design. This document is only its witness.* 🔥
