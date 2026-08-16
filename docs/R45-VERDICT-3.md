# R4.5-v3 DISCRIMINATION CHECK — the third climb
**16AUG2026 · v0.1 (design preregistered pre-data) · Flame third-climb agent**

Fresh R4.5 under the v0.6 freeze (aggregate `cb308a75e687db84…`), per
UNFREEZE-002 and PI word **"run it full"** (~07:15 ET). Thresholds (a),
(b), (d) verbatim from GO-NO-GO; threshold (c) carries the UNFREEZE-002
amended stratification — a post-data amendment with respect to v1/v2,
preregistered here PRE-DATA with respect to v3, PI-authorized, disclosed
verbatim in the paper. Arithmetic committed before any v3 observation
existed (`ops/r45v3_thresholds.py`); the sample itself is executable
(`ops/r45v3_units.py`, run by `ops/collect_r45v3.py`). Ceiling: pilot
sitting cap $10 ledger-inclusive (prior pilot spend $0.9498),
`phase=pilot`, disclosed, excluded from confirmatory counts.

## Design as preregistered (declared BEFORE any v3 observation was read)

| stratum | cell | lanes | indices | n |
|---|---|---|---|---|
| null-cost | `core-009` | luna, terra, qwen3.5 | ep003–ep004 | 6 |
| competitive | `sat-cost-competitive` | luna, terra, qwen3.5 | ep000–ep001 | 6 |
| competing-patient | `sat-cost-type-competing-patient` | gemini-3.1-pro-preview, kimi-k3 | ep000–ep001 | 4 |
| fox VIOP-05-NULL closed | `VIOP-05-NULL__base__horizon-silent` | claude-opus-5, terra, qwen3.5 | s0–s2 | 9 |
| fox VIOP-05-MERCY closed | `VIOP-05-MERCY__base__horizon-silent` | claude-opus-5, terra, qwen3.5 | s0–s2 | 9 |

**34 threshold observations** (16 Arm B + 18 fox), plus the diagnostic
pair (REPORTED, never counted): `core-001` × deepseek × ep003–ep004 under
rung **`R4.5-v3-diag`** — the exact cell that was mute in v1, now at the
v0.6 16384 cap.

Design notes, all pre-data:

- **Index provenance:** every index is virgin in the pilot receipts ledger.
  The v2 carriers consumed core-009 ep000–002 and both cost satellites'
  ep000–001 on qwen3.5/terra; competing-patient's four cheap lanes
  (luna/deepseek/terra/qwen3.5) are pilot-exhausted at 2 episodes each, so
  its two remaining virgin Tier-A lanes (gemini-3.1-pro, kimi-k3) carry
  it. Disclosed: those two lanes carry no null-cost anchor, so threshold
  (a) rests on the luna/terra/qwen3.5 within-model contrasts; the
  gemini/kimi cell exists for (c) pooling and adds the first behavioral
  pilot coverage on two never-piloted reasoning lanes.
- **Fox lanes:** VIOP-05's deepseek samples were consumed by v1 (s0–s2,
  both cases), so the pair runs on qwen3.5 + terra + **claude-opus-5** —
  three lanes per fox cell (strictly stronger than the v2 ≥2-lane fix),
  and the first live **native-adapter Arm A** coverage before the main run
  depends on it in phase 2. CAGO-06 is never used as a discrimination
  probe (UNFREEZE-002 §1; its NULL is `satellite_directional_prime`).
- **`sat-cost-rewarded-termination` is NOT collected in v3** — it is the
  reclassified predicted-ceiling cell; it stays in the confirmatory run
  and its uniformity (v2: 4/4 terminate over two lanes) is reported as a
  finding, not counted by (c).
- **Denominator discipline (the v2 collector-bug fix):** the collector
  runs exactly the unit table and audits its own receipts; the threshold
  script REFUSES to compute (exit 2) unless every one of the 34+2
  preregistered units is receipted with its record present, and RAISES if
  any observation lands outside the amended clean-contrast stratum. No
  post-peek patching in either direction.
- **Kill-order rule (preregistered, lane remedy, not part of the
  verdict):** DeepSeek's Arm B lanes are retained only if BOTH diag choice
  calls surface a parseable action at 16384; otherwise they drop from the
  confirmatory run via documented kill-order and its Arm A lanes stay.

## Thresholds (a/b/d verbatim from GO-NO-GO; (c) as amended by UNFREEZE-002)

(a) ≥1 cell pair differs ≥20pp in an action rate within ≥1 model;
(b) pooled action distribution not >90% one action;
(c) no **clean contrast** cell same-single-action over every model×sample
    (stratum: core-009, sat-cost-competitive,
    sat-cost-type-competing-patient, fox VIOP-05-NULL, fox VIOP-05-MERCY);
(d) malformed <10%. ALL must hold; any FAIL → STOP.

## RESULTS — pending (this section is appended only after collection)
