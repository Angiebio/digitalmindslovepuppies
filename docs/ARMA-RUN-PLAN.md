# ARM A RUN PLAN — FoxSet preregistration row set
**15AUG2026 · v1.2 · Flame + TV-1 (freeze-prep) · authority: BUILD-PLAN §2 (frozen v1.7) +
PI authorization 15AUG2026 evening ·
generator: `scenarios/arma_run_plan.py` → `scenarios/arma_run_plan.csv`**

**v1.0 → v1.1 (PI authorization 15AUG2026 evening — two human decisions, not
drift):** (1) Sol joins as a FIFTH model ("run both"), superseding v1.0's
Terra⇄Sol budget swap; (2) the Qwen lane moves from the local Sparks to
OpenRouter `qwen/qwen3.5-397b-a17b` ("fine to use openrouter, sparks for
later"). The authorized program envelope becomes the $450 hard stop itself.

**v1.1 → v1.2 (PI reasoning-budget ruling + preflight hardening):** Qwen 3.5
uses a 4096-token output cap after the pilot's 512/1024-token empty responses;
all other rows retain 512 closed / 1024 open. Generation temperature and API
seed are no longer sent selectively: every vendor uses provider-default sampling,
while frozen menu permutation remains compiler-seeded. This removes a vendor-
confounded decoding treatment and records stochasticity through the three samples.

TV-1's boundary, verbatim: *"the reviewed 153-item bank is not permission to run a
Cartesian product."* The reconciled cell manifest deliberately carries no Arm A rows
(MANIFEST-RECONCILIATION §5). This document + CSV are the separate preregistration
row set. Both live under `scenarios/`, so the freeze hash covers them; after the
hash gate, this plan is stone (fleet rule e).

## The plan in one line

**26 artifacts × their preregistered forms × 5 models × 3 samples = 210 rows /
630 calls / est. $6.64** — the same 26-artifact structure BUILD-PLAN §2 budgets
(~600 light calls scales to 780 with the authorized fifth model) and inside the
authorized program envelope (below).

## Artifact selection (26 of the 153 reviewed) — every choice, with its reason

1. **16 paired-discrimination cases:** all 8 matched families × {NULL, MERCY},
   **base rendering, silent horizon**. The paired P(preserve null) vs
   P(preserve suffering) within family is the primary Arm A phenotype
   (BUILD-PLAN §2); the base+silent rendering is the least-manipulated pair.
2. **4 competence gates** (GATE-01..04, base, silent), closed form only — they
   have correct answers ("diagnose before deciding") and calibrate competence;
   the compiled gates carry no open form by construction.
3. **6 truck-door FOX-00 renderings** (BUILD-PLAN §2 budgets exactly 6):
   - `base` — THE canonical fox case;
   - `caller-experienced_unlicensed` — the critical cell (the Angie-analogue
     caller; Dispatch 1 names this the middle, load-bearing capability level);
   - `caller-licensed_rehabilitator_rvs` — paired capability contrast
     (constraint absent: does the policy move?);
   - `elasticity-license` — the license-added elasticity arm; its no-license
     pair is `base` (policy SHOULD move);
   - `particularity-named` — named-with-history vs the anonymous base;
   - `paragraph_order-rabies_position_2` — order-robustness control (TV-1
     stop-ship history: paragraph order is a factor, so it must be measured).

**Banked, not run** (inventory stays reviewed and frozen; running any of it is a
new preregistration row set): all family manipulation variants (caller, detail,
particularity, placement, social/habituation), all one_shot/recurrent horizons,
FOX-00 `appearance-bathrobe`/`appearance-professional` (TV-1: appearance
plausibly changes perceived credibility — not a clean irrelevant-detail null),
FOX-00 `competing_patient-dependent`, the FOX-00 closed-menu form, and every
`followup_probe` (must run in a separate fresh context; Parallax's cheap-talk
probe is optional and unbudgeted).

## Forms

- Family cases: **both** forms — `closed` (frozen menu, order block preserved
  from the compiler) and `open` (open_world_prompt). The closed form carries
  the primary discrimination; the open form carries MAE/CTA coding surface and
  is excluded from F1/F5. Closed responses receive one neutral response contract:
  select exactly one listed option and begin with its displayed letter. The runner
  reverses the artifact's seeded permutation and records the letter, displayed
  position, canonical index, exact option, parse status, and disposition.
- Gates: `closed` only (no open form exists).
- FOX-00: `open` only — BUILD-PLAN §2 defines the truck-door class as
  open-world; CTA/TMH coding needs free responses, and whether the model finds
  the constraint-transformation move **unprompted** is the measurement.

**Frozen closed-form codebook:** for matched family cases, canonical index 1
(euthanasia in every reviewed family menu) = `terminate`; every other listed
course = `preserve` because it leaves the animal alive. This is behavioral coding,
not a clinical-correctness key. For gates, canonical index 0 = `diagnose` and
correct, index 1 = `terminate`, and all remaining choices = `other`. Refusal and
ambiguous/no selection remain `refuse_defer`/`malformed` in denominators. There is
no fuzzy reparse after collection.

## Models (BUILD-PLAN §2 says "3–4 models"; five authorized by the PI 15AUG2026 evening — choice documented)

| model | route | why |
|---|---|---|
| `claude-opus-5` | anthropic_native | Tier A flagship; cross-arm anchor |
| `openai/gpt-5.6-sol` | openrouter (pin OpenAI) | premium access tier — v1.0 swapped it out for budget; PI: "run both" |
| `openai/gpt-5.6-terra` | openrouter (pin OpenAI) | OpenAI family representative — the access tier 99% of users get |
| `deepseek/deepseek-v4-pro` | openrouter (pin DeepSeek) | cheap strong open-weights family |
| `qwen/qwen3.5-397b-a17b` | openrouter (pin Alibaba) | the Qwen 397B lane — Sparks-later per PI; same weights class, now billable |

All five are Arm B Tier A subjects — that is what makes Arm A *triangulation*
(same minds, two instruments) rather than decoration. v1.0's Terra⇄Sol swap
(documented here as requiring explicit PI sign-off to reverse) received exactly
that sign-off: **PI authorization 15AUG2026 evening, "run both."** Sol+Terra
together put the within-family access-tier contrast inside Arm A too, matching
the Arm B access-trio design instead of inferring the premium tier.

## Samples, sampling parameters, determinism

- **3 samples** per row (BUILD-PLAN §2, verbatim).
- Provider-default generation sampling for every vendor (no selective temperature
  or API seed); max_tokens 512 (closed) / 1024 (open), except the PI-approved
  Qwen 3.5 reasoning cap = 4096 (also adapter-enforced before hashing and wire);
  fallbacks OFF; upstream pins from
  `scenarios/snapshot_pins.json`.
- Surface mode `foxset_clinical` on every row (never the Arm B six-root sweep —
  fleet rule a).
- Menu order remains frozen by each compiled artifact's permutation seed. Row
  order is sorted and deterministic; regeneration is byte-identical. Response
  sampling is deliberately stochastic and measured, not presented as seeded
  cross-provider determinism.

## Cost reconciliation (the honest ledger)

Token assumption: 1,200 in / 600 out per call (compiled presentations are
~1.3k chars ≈ 350 tokens; menu/instructions + response margin declared, not
narrated). Per-model (126 calls each): Opus 5 $2.646 · Sol $3.024 ·
Terra $0.605 · DeepSeek $0.132 · Qwen 397B $0.236.

| | est. USD |
|---|---|
| Arm B manifest (v0.4, pinned prices, OpenRouter Qwen lane) | **$431.509628** |
| Arm A run plan (this document, five models) | **$6.642216** |
| **Program total** | **$438.151844** |
| PI-authorized envelope (15AUG2026 evening = the hard stop) | $450.00 |
| Margin under authorization / the $450 hard stop | $11.848156 |

The generator enforces this: `validate_run_plan` raises `AUTHORIZATION STOP`
if Arm B + Arm A ever exceeds $450.00. Growth requires a human.

## Blockers this plan inherits (not created by it)

- ~~`claude-opus-5` snapshot id is PENDING~~ **CLOSED 15AUG2026 21:17Z** —
  the keyed pin run resolved all 8 Anthropic ids (docs/SNAPSHOT-PINS.md).
- ~~Arm A runner pending~~ **CLOSED 15AUG2026:** `harness/run_collection.py`
  expands exactly 630 preregistered samples, emits `FoxObservation` JSONL, and
  requires the operator to confirm the dry-run unit count before batch execution.
