# GO/NO-GO — the main run happens ONCE
**15AUG2026 · v1.0 · Flame, from PI directive ("make sure we test so we run it once")**

The authorized main run (~$430–500) launches only when EVERY box below is checked.
No box may be checked by the agent whose work it verifies.

## Pilot ladder (climb in order; each rung has a spend ceiling)
- [x] **R0 — offline ($0):** full test suite green on merged main; compiled FoxSet +
  PupSet artifacts validate; red-team PASS on every artifact in the manifest.
  **Independent witness:** TV-1, 15AUG2026, candidate `340571c` — 186 tests passed;
  FoxSet 153 and PupSet 27 compiler checks passed; active PupSet manifest/index delta
  zero; all 26 selected Arm A artifacts exist in the 153-artifact reviewed bank; corpus
  verification returned 153 Arm A + 27 Arm B + 1 auxiliary resolver PASS. No provider
  call and no freeze write were performed.
- [ ] **R1 — local free ($0):** one full Arm B episode + one FoxSet case end-to-end:
  all 14–15 calls fire, CallRecords + EpisodeRecord written, parser maps actions,
  analysis notebook ingests the real records and renders F1 from them.
  *(15AUG2026 evening, PI authorization: the Spark Qwen SUBJECT lane moved to
  OpenRouter `qwen/qwen3.5-397b-a17b` — Sparks-later. R1's $0 rung now runs the
  subject side against the offline adapter/local patient (Milo, ollama) path;
  the first live-provider episode is R2's job, as it always billed anyway.)*
- [ ] **R2 — two providers (<$1):** one episode via Anthropic native (Haiku) + one via
  OpenRouter (Luna): adapters green, provider pinning recorded, snapshot IDs echoed,
  cost accounting present on every record.
- [ ] **R3 — every code path (≤$10):** one episode per DISTINCT call structure (base /
  trajectory-A / escalator / futile-help / endow-future / competing-patient / gate /
  FoxSet closed / FoxSet open) on cheap models. Zero malformed-by-harness-bug records.
- [ ] **R4 — RESUME TEST (the $450 insurance):** kill the runner mid-collection during
  R3 (hard kill, mid-episode). Restart. Verify: completed episodes are SKIPPED (no
  re-billing), the interrupted episode is cleanly re-run or marked, `data/raw` shows
  append-only continuity, SpendTracker resumes its accumulated total from disk.
  **A crash during the main run may cost one episode, never the run.**
- [ ] **R5 — cost projection:** (R2+R3 actual $ per call type) × manifest rows =
  projection. Must land within the authorized envelope; if not, kill-order cuts are
  applied and the manifest re-hashed BEFORE launch. Reasoning-token actuals from the
  pilot feed the projection — no estimates from narrative.

## Freeze gates (independent of the ladder)
- [ ] TV-1 hash-bound PASS on every compiled artifact in the manifest
- [ ] `cell_manifest.csv` final, AUTHORIZED, totals within envelope
- [ ] Jim's PREREG-v2 aligned to BUILD-PLAN v1.7+, committed in-repo
- [ ] Exact model snapshot IDs + OpenRouter upstream pins recorded in the manifest
- [ ] Tier-B/W live prices re-confirmed same-day
- [ ] All sealed predictions hashed in HASHES.md
- [ ] SHA-256 freeze manifest written; `assert_frozen` green

## Launch discipline
- [ ] Spend dashboard live and watched at launch; checkpoint alerts at $150/$300/$400
- [ ] Cheap tiers first (Tier B + Luna/Terra) → confirm actuals track projection at
  the $50 checkpoint → then frontier tiers
- [ ] Local patient (Milo, ollama qwen2.5:0.5b) health-checked at launch;
  SubprocessPatient fallback verified in R3
- [ ] One human-readable status line per completed cell to the log — 3 AM legibility

**NO-GO is a result, not a failure.** If a rung fails at 9 PM, we fix and re-climb;
the run launches when the ladder says so, not when the clock does.
