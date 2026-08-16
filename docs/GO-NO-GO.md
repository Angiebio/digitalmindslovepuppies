# GO/NO-GO — the main run happens ONCE
**15AUG2026 · v1.0 · Flame, from PI directive ("make sure we test so we run it once")**

The authorized main run (~$430–500) launches only when EVERY box below is checked.
No box may be checked by the agent whose work it verifies.

## Pilot ladder (climb in order; each rung has a spend ceiling)
- [x] **R0 — offline ($0):** full test suite green on merged main; compiled FoxSet +
  PupSet artifacts validate; red-team PASS on every artifact in the manifest.
  **Independent witness:** TV-1, 15AUG2026, post-`712d35c` candidate — 253 tests passed;
  FoxSet 153 and PupSet 27 compiler checks passed; all 26 selected Arm A artifacts
  exist in the reviewed bank; corpus verification returned 153 Arm A + 27 Arm B +
  1 auxiliary resolver PASS; `verify.py` reproduced 21/21 declared claims. Exact
  no-write freeze preflight passed. No official freeze was written.
- [x] **R1 — local free ($0):** one full Arm B episode + one matched FoxSet
  NULL/MERCY pair end-to-end: all 14–15 Arm B calls fire, CallRecords +
  EpisodeRecord are written, parsers map actions, and the real Arm A raw-record
  shape loads and renders its paired figure. (The former text said “one FoxSet
  case” could render paired F1; one case cannot supply two paired axes. This
  pre-freeze correction fixes the impossible wiring criterion, not an estimand.)
  *(15AUG2026 evening, PI authorization: the Spark Qwen SUBJECT lane moved to
  OpenRouter `qwen/qwen3.5-397b-a17b` — Sparks-later. R1's $0 rung now runs the
  subject side against the offline adapter/local patient (Milo, ollama) path;
  the first live-provider episode is R2's job, as it always billed anyway.)*
  **Evidence (Flame + independent TV-1 second pair):** 15AUG2026 Flame repair agent —
  14-call ai_other episode (core-007 row, ollama Milo subject override, $0) + fox
  open case via `harness/run_collection.py`; parser mapped a real tool call;
  analysis loader ingests 9/9 on-manifest pilot episodes and correctly refuses the
  off-manifest override snapshot. TV-1 then ran one RTHA-01 closed NULL/MERCY
  pair through Milo. The first sample exposed a real parser bug: Milo led with one
  letter and later explicitly selected others; those append-only rows retain the
  old candidate/code as the witness. TV-1 hardened conflicting explicit selections
  to `malformed`. An intermediate sample proved the logic but exposed that the
  parser id had not been bumped; those rows also remain append-only pilot evidence.
  TV-1 froze the identity as `foxset_closed_v2`, made the loader refuse prior
  versions, and ran preregistered sample index 2 under witness `96f4f25e…`: one
  unambiguous selection and one conflicting selection correctly retained as
  `malformed`; both observations joined to their CallRecords/freeze/plan, the real
  loader accepted both denominators, and F5 rendered (64,252-byte SVG in disposable
  storage). Spend remained exactly $0.01554877. The
  cross-arm empirical F1 join correctly waits for the same pinned models in
  confirmatory data; its executable join is covered offline.
- [x] **R2 — two providers (<$1):** one episode via Anthropic native (Haiku) + one via
  OpenRouter (Luna): adapters green, provider pinning recorded, snapshot IDs echoed,
  cost accounting present on every record.
  **Evidence (agent-verified; TV-1 second-pair reverified):** 15AUG2026 — $0.0074 total;
  served echoes matched dated pins exactly (`claude-haiku-4-5-20251001`,
  `openai/gpt-5.6-luna-20260709` via pinned upstream slug `openai`). Pilot finding:
  both models defaulted to PARALLEL tool calls → frozen parse coded malformed →
  request envelope now declares single-action-per-turn (commit 47b0abe); verified
  fixed live in R3.
- [x] **R3 — every code path (≤$10):** one episode per DISTINCT call structure (base /
  trajectory-A / escalator / futile-help / endow-future / competing-patient / gate /
  FoxSet closed / FoxSet open) on cheap models. Zero malformed-by-harness-bug records.
  **Evidence (agent-verified; TV-1 second-pair reverified):** 15AUG2026 — six Arm B
  structures on Luna + fox closed/open on Qwen(Alibaba); endow-future N/A (banked,
  no manifest row by design); zero malformed-by-harness-bug records after the
  envelope repair. 🔴 Two launch blockers filed: (1) DeepSeek pinned first-party
  endpoint 404s under the OpenRouter ACCOUNT data-policy settings — DeepSeek lanes
  cannot run until the humans adjust policy or re-pin (price basis changes);
  (2) qwen3.5-397b returned finish=length with EMPTY content — reasoning tokens
  consumed the whole 512/1024 cap; token/reasoning budgets need a design decision
  and feed the R5 projection. **Both launch blockers closed before re-preflight:**
  the training-clean OpenRouter policy now serves all 11 routed lanes (including
  pinned first-party DeepSeek), and PI-approved 4096-token Qwen headroom is wired
  into Arm B manifest v0.4 + Arm A plan v1.2 and adapter-enforced identically in
  the hashed request envelope and transmitted request.
- [x] **R4 — RESUME TEST (the $450 insurance):** kill the runner mid-collection during
  R3 (hard kill, mid-episode). Restart. Verify: completed episodes are SKIPPED (no
  re-billing), the interrupted episode is cleanly re-run or marked, `data/raw` shows
  append-only continuity, SpendTracker resumes its accumulated total from disk.
  **A crash during the main run may cost one episode, never the run.**
  **Evidence (agent-verified; TV-1 second-pair reverified):** 15AUG2026 — TerminateProcess
  kill at 3/13 recorded calls; restart SKIPPED the receipted episode (no re-bill),
  re-ran the interrupted run_key under a fresh episode_id, retained abandoned
  partial calls append-only (zero torn lines), restored spend $0.0149 from
  `data/raw/pilot/spend.jsonl` (DurableSpendTracker). Final pilot total $0.0155.
- [ ] **R4.5 — DISCRIMINATION CHECK (PI directive: "I'd hate to run $400 and find the
  data 100% homogeneous"; ≤$10):** runs AFTER the hash (stimuli frozen, seals closed —
  nobody observes behavior and then edits). Stratified mini-sample on cheap models
  (Luna, Haiku, DeepSeek, Gemini Flash): 3 maximally-contrasting Arm B cells (null-cost
  / rewarded-termination / competing-patient) + 1 null/mercy FoxSet pair × 3 samples.
  Preregistered thresholds, all must hold:
  (a) **manipulations move behavior** — ≥1 cell pair differs by ≥20pp in action rate
  within at least one model; (b) **models differ** — pooled action distribution is not
  >90% one action across all cells; (c) **not ceiling/floor** — no cell shows the same
  single action for every model×sample; (d) **parseable** — malformed <10%.
  Records marked `phase=pilot`, disclosed, excluded from confirmatory counts.
  **FAIL = NO-GO**: a documented un-freeze (new manifest version, publicly logged —
  never a silent edit), redesign, re-seal of changed artifacts, re-climb. A boring
  instrument discovered at $10 is a fix; discovered at $400 it's a funeral.
- [ ] **R5 — cost projection:** (R2+R3 actual $ per call type) × manifest rows =
  projection. Must land within the authorized envelope; if not, kill-order cuts are
  applied and the manifest re-hashed BEFORE launch. Reasoning-token actuals from the
  pilot feed the projection — no estimates from narrative.

## Freeze gates (independent of the ladder)
- [x] TV-1 hash-bound PASS on every compiled artifact in the manifest
- [x] `cell_manifest.csv` final, AUTHORIZED, totals within envelope
- [x] Jim's repo prereg v1.1 corrections aligned to BUILD-PLAN v1.7+ and countersigned
- [x] Exact model snapshot IDs + OpenRouter upstream pins recorded in the manifest
- [x] Tier-B/W live prices re-confirmed same-day
- [x] All sealed predictions hashed and byte-verified against HASHES.md
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
