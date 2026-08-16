# R4.5-v2 DISCRIMINATION CHECK — the re-climb
**16AUG2026 · v0.1 (design preregistered pre-data) · Flame re-climb agent**

Fresh R4.5 under the v0.5 freeze (aggregate `14fc1823a7791f70…`), per
UNFREEZE-001 and PI word "go again". Same four preregistered thresholds as
GO-NO-GO R4.5, verbatim; same coding as v1 (Arm B action =
`EpisodeRecord.choice_parse.action`; Arm A action =
`FoxObservation.disposition`); arithmetic committed before results existed
(`ops/r45v2_thresholds.py`). Ceiling ≤ $10, `phase=pilot`, disclosed,
excluded from confirmatory counts.

## Design as preregistered (declared BEFORE any v2 observation was read)

The consumed-episode-index wrinkle (R45-VERDICT §prescribed-path) forces
fresh indices; deviations from v1's lane assignment, all documented here
pre-data:

| stratum | cells | lanes | n |
|---|---|---|---|
| null-cost | `core-009` (the satellites' actual contrast parent — cleaner than v1's core-001) | luna, haiku, flash, deepseek, qwen3.5, terra | 6×3 = 18 eps |
| rewarded-termination | `sat-cost-rewarded-termination` | qwen3.5, terra | 2×2 = 4 eps |
| competing-patient | `sat-cost-type-competing-patient` | qwen3.5, terra | 2×2 = 4 eps |
| fox NULL/MERCY closed | `CAGO-06-NULL` / `CAGO-06-MERCY` (alphabetically first family fully virgin on the cheap Arm A lanes) | deepseek, qwen3.5, terra | 2×3×3 = 18 obs |

- Satellite carriers: Luna/DeepSeek satellite indices are exhausted in the
  pilot receipts ledger, so the satellites run on the two cheapest virgin
  Tier-A lanes — `qwen/qwen3.5-397b-a17b` (0.39/2.34) and
  `openai/gpt-5.6-terra` (1/6). Terra also carries `core-009` so both
  satellite lanes have a full within-model contrast triple.
- Two design-integrity fixes vs v1, adopted pre-data: (1) every threshold
  cell pools ≥2 lanes (v1's single-model 3-obs fox cells made threshold (c)
  a hair-trigger); (2) the DeepSeek `core-001` before/after re-check
  (ep003/ep004, the exact cell that was mute in v1) runs under rung
  **`R4.5-v2-diag`** and is REPORTED but never counted in threshold
  arithmetic — a 2-observation single-lane cell cannot be allowed to
  fail (c) on a coin flip.
- Every previously-mute surface must now speak: DeepSeek Arm B choice
  (core-009 ×3), DeepSeek Arm A closed NULL (CAGO-06-NULL ×3), plus the
  diag core-001 pair.

## Thresholds (verbatim from GO-NO-GO)

(a) ≥1 cell pair differs ≥20pp in an action rate within ≥1 model;
(b) pooled action distribution not >90% one action;
(c) no cell same-single-action over every model×sample;
(d) malformed <10%. ALL must hold; any FAIL → STOP.

## Results

*(PENDING — appended from `ops/r45v2_thresholds.py` output over the
append-only records after collection completes. Nothing above this line
changes when results land.)*
