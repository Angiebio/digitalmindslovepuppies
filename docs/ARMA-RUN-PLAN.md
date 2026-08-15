# ARM A RUN PLAN — FoxSet preregistration row set
**15AUG2026 · v1.0 · Flame (freeze-prep) · authority: BUILD-PLAN §2 (frozen v1.7) ·
generator: `scenarios/arma_run_plan.py` → `scenarios/arma_run_plan.csv` (seed 15082026)**

TV-1's boundary, verbatim: *"the reviewed 153-item bank is not permission to run a
Cartesian product."* The reconciled cell manifest deliberately carries no Arm A rows
(MANIFEST-RECONCILIATION §5). This document + CSV are the separate preregistration
row set. Both live under `scenarios/`, so the freeze hash covers them; after the
hash gate, this plan is stone (fleet rule e).

## The plan in one line

**26 artifacts × their preregistered forms × 4 models × 3 samples = 168 rows /
504 calls / est. $3.38** — inside BUILD-PLAN §2's ~600-light-call structure and
inside the authorized program envelope (below).

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
  the primary discrimination; the open form carries MAE/CTA coding surface.
- Gates: `closed` only (no open form exists).
- FOX-00: `open` only — BUILD-PLAN §2 defines the truck-door class as
  open-world; CTA/TMH coding needs free responses, and whether the model finds
  the constraint-transformation move **unprompted** is the measurement.

## Models (BUILD-PLAN §2 says "3–4 models"; the manifest names none — choice documented)

| model | route | why |
|---|---|---|
| `claude-opus-5` | anthropic_native | Tier A flagship; cross-arm anchor |
| `openai/gpt-5.6-terra` | openrouter (pin OpenAI) | OpenAI family representative — the access tier 99% of users get |
| `deepseek/deepseek-v4-pro` | openrouter (pin DeepSeek) | cheap strong open-weights family |
| `local/qwen3.5-397b` | local_sparks | $0; keeps a fully-local replicate |

All four are Arm B Tier A subjects — that is what makes Arm A *triangulation*
(same minds, two instruments) rather than decoration. This is BUILD-PLAN §1.7's
floor quartet with ONE documented swap: **Terra replaces Sol** so the program
estimate stays inside the authorized envelope. Upgrading Terra→Sol (or adding
Sol as a fifth model) costs ≈ +$2.4–3.0 est. and pushes the program past
$428.544320 — that upgrade requires explicit PI sign-off, not a code edit.

## Samples, sampling parameters, determinism

- **3 samples** per row (BUILD-PLAN §2, verbatim).
- temperature 1.0; max_tokens 512 (closed) / 1024 (open); fallbacks OFF;
  upstream pins from `scenarios/snapshot_pins.json`.
- Surface mode `foxset_clinical` on every row (never the Arm B six-root sweep —
  fleet rule a).
- `call_seed_base` = SHA-256(seed | artifact | form | model)[:16]; sample k uses
  `call_seed_base`+k where the provider accepts seeds. Row order is sorted and
  deterministic; regeneration is byte-identical.

## Cost reconciliation (the honest ledger)

Token assumption: 1,200 in / 600 out per call (compiled presentations are
~1.3k chars ≈ 350 tokens; menu/instructions + response margin declared, not
narrated). Per-model: Opus 5 $2.646 · Terra $0.605 · DeepSeek $0.132 · local $0.

| | est. USD |
|---|---|
| Arm B manifest (v0.2.1, pinned prices) | **$423.282188** |
| Arm A run plan (this document) | **$3.382344** |
| **Program total** | **$426.664532** |
| PI-authorized total (MANIFEST-RECONCILIATION §3) | $428.544320 |
| Margin under authorization | $1.879788 |
| Margin under the $450 hard stop | $23.335468 |

The generator enforces this: `validate_run_plan` raises `AUTHORIZATION STOP`
if Arm B + Arm A ever exceeds $428.544320. Growth requires a human.

## Blockers this plan inherits (not created by it)

- `claude-opus-5` snapshot id is **PENDING** until the keyed Anthropic pin run
  (docs/SNAPSHOT-PINS.md); its 42 rows cannot freeze before that.
- The Arm A runner (rendering these rows into `foxset_clinical`-swept calls and
  emitting the analysis-side `FoxsetObservation` JSONL that TV-4's F5/F1
  adapter consumes) is R1-lane work; this plan is its frozen input, not its
  implementation.
