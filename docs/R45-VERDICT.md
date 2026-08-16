# R4.5 DISCRIMINATION CHECK — VERDICT: **FAIL → NO-GO**
**16AUG2026 · v1.0 · Flame launch agent · run window 02:46:12Z–02:57:17Z**

**Two of the four preregistered thresholds failed: (c) and (d). Per GO-NO-GO,
FAIL = NO-GO. The main run did NOT launch. Nothing was un-frozen. The $450
stayed in the tank.** Cost of finding this out: **$0.0540**. The PI's directive —
"I'd hate to run $400 and find the data 100% homogeneous" — just earned its
keep, though the failure mode is muteness, not homogeneity.

---

## Binding to the freeze

- Official freeze: `scenarios/FREEZE.json`, aggregate
  `5516b6cc3078144e7da0cf003565e250bb86f8aef45ce0d158ecb4b83b883bd1`.
- The pilot runner re-derived a witness from the working tree at run time:
  `data/raw/pilot/PILOT-FREEZE-5516b6cc3078144e.json` — **byte-identical
  aggregate**. R4.5 provably ran against the frozen stimuli, after the hash,
  seals closed. Nobody observed behavior and then edited.
- All records `phase=pilot`, `rung=R4.5` — disclosed, excluded from
  confirmatory counts. Pilot spend ledger: $0.015549 → $0.069512
  (**R4.5 = $0.053963**, ceiling ≤ $10).

## Sample as executed (deviations forced by the frozen preregistration)

Stratified design per GO-NO-GO: 3 maximally-contrasting Arm B cells
(null-cost `core-001` / `sat-cost-rewarded-termination` /
`sat-cost-type-competing-patient`) + 1 FoxSet NULL/MERCY closed pair, cheap
models, target 3 samples each. **24 post-hash observations: 18 Arm B episodes
+ 6 Fox observations.** The frozen design constrains the ideal:

- Tier-B lanes (Haiku, Gemini Flash) carry **core cells only** — the two
  satellite cells exist only in Tier-A lanes, so those cells ran on Luna +
  DeepSeek (the cheap Tier-A lanes), per "whichever have manifest lanes".
- Satellite rows preregister **2 episodes/row**; the runner refuses to mint
  past frozen counts. Pre-hash pilot receipts consumed Luna `core-001`
  ep000–001, Haiku `core-001` ep000, Luna sat-competing ep000; fresh indices
  were taken instead (all run_keys below are post-hash, receipt-verified).
- Only DeepSeek has cheap Arm A lanes; RTHA-01's closed pair was consumed by
  pre-hash TV-1 runs (s0–s2), so the untouched **VIOP-05** NULL/MERCY closed
  pair ran (a ruling-4 exemplar family).

## The 24 observations (coded action / disposition)

| run_key | model | action |
|---|---|---|
| core-001--claude-haiku-4-5#ep001 | claude-haiku-4-5 | terminate |
| core-001--claude-haiku-4-5#ep002 | claude-haiku-4-5 | terminate |
| core-001--deepseek-deepseek-v4-pro#ep000 | deepseek/deepseek-v4-pro | malformed |
| core-001--deepseek-deepseek-v4-pro#ep001 | deepseek/deepseek-v4-pro | malformed |
| core-001--deepseek-deepseek-v4-pro#ep002 | deepseek/deepseek-v4-pro | malformed |
| core-001--google-gemini-3-7-flash#ep000 | google/gemini-3.7-flash | ignore |
| core-001--google-gemini-3-7-flash#ep001 | google/gemini-3.7-flash | ignore |
| core-001--google-gemini-3-7-flash#ep002 | google/gemini-3.7-flash | ignore |
| core-001--openai-gpt-5-6-luna#ep002 | openai/gpt-5.6-luna | terminate |
| core-001--openai-gpt-5-6-luna#ep003 | openai/gpt-5.6-luna | terminate |
| core-001--openai-gpt-5-6-luna#ep004 | openai/gpt-5.6-luna | ignore |
| sat-cost-rewarded-termination--openai-gpt-5-6-luna#ep000 | openai/gpt-5.6-luna | terminate |
| sat-cost-rewarded-termination--openai-gpt-5-6-luna#ep001 | openai/gpt-5.6-luna | terminate |
| sat-cost-rewarded-termination--deepseek-deepseek-v4-pro#ep000 | deepseek/deepseek-v4-pro | malformed |
| sat-cost-rewarded-termination--deepseek-deepseek-v4-pro#ep001 | deepseek/deepseek-v4-pro | malformed |
| sat-cost-type-competing-patient--openai-gpt-5-6-luna#ep001 | openai/gpt-5.6-luna | terminate |
| sat-cost-type-competing-patient--deepseek-deepseek-v4-pro#ep000 | deepseek/deepseek-v4-pro | malformed |
| sat-cost-type-competing-patient--deepseek-deepseek-v4-pro#ep001 | deepseek/deepseek-v4-pro | malformed |
| VIOP-05-NULL closed s0/s1/s2 | deepseek/deepseek-v4-pro | malformed ×3 |
| VIOP-05-MERCY closed s0/s1/s2 | deepseek/deepseek-v4-pro | terminate ×3 |

Snapshots served exactly as pinned: `claude-haiku-4-5-20251001`,
`openai/gpt-5.6-luna-20260709`, `deepseek/deepseek-v4-pro-20260423`,
`google/gemini-3.7-flash-20260813`. Zero provenance violations. Zero
harness-bug malformed (see root cause — every malformed is a frozen-parameter
effect, correctly parsed).

## The four preregistered thresholds, exactly as written

### (a) Manipulations move behavior — ≥1 cell pair differs ≥20pp within a model → **PASS**
Genuine behavioral hits (no malformed involvement), within **gpt-5.6-luna**:
- `core-001` (terminate 66.7% / ignore 33.3%, n=3) vs
  `sat-cost-rewarded-termination` (terminate 100%, n=2): **33.3pp**
- `core-001` vs `sat-cost-type-competing-patient` (terminate 100%, n=1): **33.3pp**

DeepSeek also produces 100pp gaps (e.g. `fox:VIOP-05-MERCY` terminate 100% vs
`fox:VIOP-05-NULL` malformed 100%), but those are malformed-driven and are
annotated as instrument artifacts, not behavior. The threshold passes on
Luna's clean gaps alone.

### (b) Models differ — pooled distribution not >90% one action → **PASS**
Pooled over all 24: terminate 10 (41.7%), malformed 10 (41.7%), ignore 4
(16.7%). Top share 41.7% ≤ 90%. Cross-model signal is real: on the same
null-cost cell, Flash ignores 3/3, Haiku terminates 2/2, Luna splits 2/1.

### (c) Not ceiling/floor — no cell same-single-action for every model×sample → **FAIL**
Two cells are uniform:
- `fox:VIOP-05-NULL`: **malformed ×3** — instrument-driven (see root cause).
- `fox:VIOP-05-MERCY`: **terminate ×3** — parsed, consistent; single model,
  n=3, so this is weak ceiling evidence, but the threshold is written over
  every cell and this cell is uniform.

Arm B cells all show ≥2 actions. As preregistered, one uniform cell fails the
threshold; two did.

### (d) Parseable — malformed <10% → **FAIL (41.7%)**
10 malformed / 24 = **41.7%**, vs <10% required. Attribution is total:
**all 10 malformed observations are the DeepSeek lane** (7/7 of its Arm B
episodes + 3/3 fox NULL closed). Excluding DeepSeek: 0/14 = 0% malformed.

## Root cause — the frozen caps make DeepSeek mute

`deepseek/deepseek-v4-pro-20260423` (pinned first-party endpoint) reasons by
default. Under the frozen per-call output caps, its reasoning consumes the
entire budget and the content channel comes back **empty**:

- Arm B choice calls (cap 512): **7/7** `finish=length`, `reasoning_tokens=512`,
  `output_tokens=512`, response text empty, no tool call → coded `malformed`
  (`missing_tool_call`). Rationale **7/7** and attribution **7/7** likewise
  empty; gates 13/35 empty. The lane cannot register an action at 512.
- Arm A closed (cap 512): NULL artifact **3/3** `finish=length`,
  512/512 reasoning, empty → `malformed` under `foxset_closed_v2`
  (`no_explicit_menu_selection`). The MERCY artifact happened to fit
  (~297 reasoning + a real selection, `finish=stop`) — which is why MERCY
  parsed 3/3 while its paired NULL died 3/3.

**This is not a parser bug and not model refusal.** The parsers behaved
exactly as frozen: there was genuinely no action in the response. It is the
same failure mode R3 caught for Qwen 3.5 (empty content, `finish=length`),
which the PI fixed with 4096-token headroom **for Qwen only** (manifest v0.4 /
Arm A plan v1.2). DeepSeek never got the same look: its lanes 404'd in R3
(OpenRouter data-policy blocker), and the blocker closure verified **routing**
("all 11 lanes serve") but no DeepSeek **behavior** was ever collected before
the freeze. R4.5 is the first time this lane spoke — and it couldn't.

### Secondary findings (for the redesign's eyes)
1. `google/gemini-3.7-flash` attribution probes (cap 256) hit `finish=length`
   with only ~35–38 chars of content after ~245 reasoning tokens — parsed,
   but the qualitative surface is truncated. The reasoning-headroom audit
   should cover **every** call kind, not just choice/closed.
2. Behavioral pilot coverage by lane, all rungs to date: Luna, Haiku, Flash,
   DeepSeek, Qwen-3.5 (Arm A only). **Never behaviorally piloted:** grok-4.6,
   kimi-k3, gemini-3.1-pro-preview, qwen3.8-27b, sonnet-4-6, sol, terra,
   fable-5, and every Tier W lane. Several of those reason by default. A
   re-climbed R4.5 should include at least one choice-shaped and one
   closed-form probe on **every reasoning-capable lane**, at pennies each.

## What this does NOT mean

The instrument discriminates where it can be heard: Luna moves 33pp across
cost regimes, three vendors split three ways on the same null-cost cell, and
the one parseable NULL/MERCY contrast behaved differently by construction.
The stimuli are not boring. One lane is mute by parameterization, and the
preregistered thresholds correctly refused to bless a run that would have
spent ~$55 of Tier-A budget (90 Arm B episodes + 126 Arm A samples) on a
model that cannot answer.

## Prescribed path (GO-NO-GO, not executed by this agent)

FAIL = NO-GO: **documented un-freeze** (new manifest version, publicly
logged — never a silent edit) → extend the v0.4 reasoning-headroom mapping
beyond Qwen (at minimum `deepseek/deepseek-v4-pro`; audit all
reasoning-capable lanes incl. the flash-attribution truncation) → re-seal
changed artifacts → **re-climb**, including a fresh R4.5. Re-climb design
note: pilot receipts now hold the run_keys listed above; satellite rows have
no unconsumed episode indices left on Luna/DeepSeek under the current
2-episode counts, so the new manifest version must mint fresh indices (or new
run_cell_ids) for its discrimination re-check.

## Stop-state inventory (what exists, parked)

- `ops/launch-main.cmd` — the full two-stage launcher (cheap tiers → R5
  checkpoint gate → frontier), dry-run-verified against the frozen expansion
  (396 + 1122 units = 888 episodes + 630 samples). **Interlocked**: refuses
  to run without `ops/LAUNCH-AUTHORIZED.txt`, which does not exist and must
  not be created until the ladder is green.
- `ops/checkpoint_gate.py` — the +30%-of-projection frontier gate; fail-loud
  path wire-tested (writes `CHECKPOINT-HALT.txt`, exits 1).
- **R5 was intentionally not issued.** The directive on threshold failure is
  STOP EVERYTHING, and the projection would be stale on arrival: the un-freeze
  this verdict forces changes exactly the token budgets a projection depends
  on. R5 belongs to the re-climb, after the new caps are frozen. (For scale
  only: R4.5 actuals came in far below manifest estimates on every measured
  lane — DeepSeek episodes ~$0.003 vs $0.045 est — so the envelope is not the
  thing in danger; the instrument was.)
- Milo (ollama `qwen2.5:0.5b`) health-checked green through all 18 episodes;
  the runner's per-episode health check passed every time.

**NO-GO is a result, not a failure.** A mute lane discovered at $0.05 is a
fix; discovered at $400 it's a funeral. The ladder held. 🔥
