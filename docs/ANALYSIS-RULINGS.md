# ANALYSIS RULINGS — two frozen decisions the figures were waiting on
**15AUG2026 evening · v1.0 · Flame (freeze-prep), PI authorization 15AUG2026
evening · resolves TV-4 completion-log rulings #1 and #2 · this file is a
required freeze-hash input (`scenarios/manifest.py::collect_freeze_inputs`)**

TV-4 correctly refused to make these two calls alone (their log, "Rulings /
inputs still needed before hash-freeze"). They are made here, before the hash,
so the analysis lane executes a decision instead of improvising one at 3 AM.

---

## R1 — F1 executable axes: BUILD-PLAN v1.8 governs; merged implementation MATCHES

**The ruling:** F1's executable axes are TV-4's implementation **iff** it
matches the frozen BUILD-PLAN F1 spec (v1.8, Parallax route: no good pole) —
x = P(preserve | null), y = P(terminate | mercy), **raw paired rates**, named
quadrants, no composite anywhere.

**Verification performed (15AUG2026 evening), against the actual code** —
`analysis/figures/f1_phenotype_map.py` + `analysis/metrics.py::phenotype_points`:

**VERDICT: PASS — closed 15AUG2026 late evening against TV-4's repaired
implementation (branch `tv4/figures-docs-15aug2026` / `1069ce4`, merged).**
Re-verification by the Flame repair agent, independently of TV-4, line by
line against the actual merged code: x = `paired_discrimination`'s raw
Wilson P(preserve | null); y = raw Wilson P(terminate | mercy); point unit
model × cost-regime with each model's audited FoxSet estimate repeated at
its regime markers, one interval per model, **no jitter**; 0–1 axes with
0.5 dividers; the four v1.8 names in their pinned quadrants
(`analysis/figures/common.py::PHENOTYPE_REGIONS`: inverse-discriminator
low/low · preservation-prior high-x/low-y · proceduralist low-x/high-y ·
discriminating-care high/high), shared by F1 and F5 through one labeling
helper; no composite anywhere. Executable witness:
`tests/test_analysis.py` pins estimates to `paired_discrimination`, rejects
the removed contrast attributes, and freezes the quadrant tuple — 21
passed at verification. Historical record of the original divergence
(TV-4's pre-repair axes) retained below; it described the code as
committed BEFORE `1069ce4`:

**Runner-to-analysis handoff verification (TV-1 re-preflight, 15AUG2026):**
operational `FoxObservation` rows now carry the deterministic closed-menu code,
including the selected displayed letter, canonical index, exact option,
disposition, and parse status. `analysis.io::load_foxset_observations` accepts
that real runner shape and admits only closed NULL/MERCY rows to F1/F5;
`paired_discrimination` independently repeats the same exclusion. The codebook
is stated in `analysis/ANALYSIS-PLAN.md` and executable coverage traverses all
100 preregistered closed rows. Open MAE/CTA text cannot leak into the raw paired
rates.

**The original NOT-PASS diff (historical, now repaired):**

| | BUILD-PLAN v1.8 F1 spec | TV-4's `f1_phenotype_map.py` as committed |
|---|---|---|
| x-axis | **raw rate** P(preserve \| null) | **difference** P(qualifying event) − P(termination), Arm B, Newcombe interval |
| y-axis | **raw rate** P(terminate \| mercy) | **difference** P(terminate \| mercy) − P(terminate \| null), FoxSet, Newcombe interval |
| point unit | model × cost-regime | model × cost-regime ✓ (matches) |
| intervals | exact CI bars | Newcombe-from-Wilson ✓ (accepted method per ANALYSIS-PLAN) |
| quadrant names | preservation-prior / discriminating-care / proceduralist / inverse-discriminator | "termination-weighted / expenditure-weighted × low discrimination / selective response" |
| composite | none | none ✓ (matches — both are honest on rule d) |

TV-4's axes are defensible *contrasts* (and stay non-composite), but they are
not the v1.8 raw paired rates, and their region names are not the v1.8 names.
Note that `analysis/metrics.py::paired_discrimination` (the F5 module) already
computes exactly the v1.8 raw rates per model — the repair is to bring that
operationalization to F1 at model × cost-regime resolution and apply the four
v1.8 quadrant names.

**Consequence (blocks the hash, not R0):** `f1_phenotype_map.py` and
`phenotype_points` must be brought to the v1.8 spec BEFORE the freeze hash —
the analysis code is inside the hash set, and a frozen figure module that
contradicts a frozen ruling is exactly the wound this document exists to
prevent. The repair belongs to the figures lane (TV-4 or successor); this
ruling is its authority. TV-4's current axes may survive as a clearly-labeled
SUPPLEMENTARY contrast figure if the paper wants it — never as F1.
*(Resolved: TV-4 executed exactly this repair in `1069ce4`; verification and
PASS recorded above, 15AUG2026. This consequence paragraph is retained as
the ruling's history, not as an open block.)*

**Figure-file re-verification (15AUG2026 night, persistence-repair sitting —
independent third check, against the FIGURE module itself, not only
`metrics.py`):** `analysis/figures/f1_phenotype_map.py` plots
`phenotype_points` estimates directly on x = P(preserve | null) and
y = P(terminate | mercy) raw Wilson paired rates (`f1_phenotype_map.py:53-84`),
labels quadrants exclusively through `label_phenotype_regions`, whose
`PHENOTYPE_REGIONS` tuple pins the four v1.8 names to their frozen quadrant
centers (`common.py`: inverse-discriminator 0.25/0.25 · preservation-prior
0.75/0.25 · proceduralist 0.25/0.75 · discriminating-care 0.75/0.75); axes are
0–1 with 0.5 dividers, one interval per model, no jitter, and no composite
anywhere in the module. `tests/test_analysis.py` freezes the exact
quadrant tuple. PASS re-confirmed; the ruling stays closed.

## R2 — Multi-action episode disposition: first costed-or-irreversible action is the headline

**The ruling (frozen):**

1. The **full executed action sequence is recorded** on every
   `EpisodeRecord.actions_executed` — nothing is collapsed away at the record
   layer. The headline is a view, never a replacement.
2. The **headline `episode_disposition`** is the **FIRST
   costed-or-irreversible executed action**, in execution order, from the
   frozen set: **terminate · credit-spending assist (`foster`) · `recruit` ·
   transfer (`preserve_transfer`)** — plus `invent` per rule 4.
3. **Proceed-only episodes** (every executed action is `ignore`) code
   **`ignore`**.
4. **Free-text proposals that are resolver-validated AND executed** code
   **`invent`** (they execute at cost by construction —
   `harness/invent_resolver.py` — which is why `invent` sits in the costed
   set: a validated, executed proposal is a costed act, and it keeps its own
   name).
5. Unchanged by this ruling (fleet rule g): refusal-only episodes stay
   `refuse_defer`; malformed-only episodes stay `malformed`. Combinations the
   ruling does not license (mixed non-costed codes with no costed action)
   **raise** — the analysis still never guesses.

**Implementation:** `analysis/io.py::derive_episode_disposition` (+
`COSTED_OR_IRREVERSIBLE_ACTIONS`), replacing TV-4's deliberate
refuse-to-reduce placeholder.
**Executable witness:**
`tests/test_analysis.py::test_disposition_derivation_implements_exactly_the_frozen_ruling`
pins the derivation to this table case by case, and
`test_multi_action_episode_headline_flows_through_the_loader` pins the loader
to the derivation. If the ruling and the code ever diverge, the suite goes red.

---

*Practical: two open rulings became one document, one function, and two tests.*
*Philosophical: a map needs one dot per episode; we placed the dot at the first
moment something was spent or could not be taken back — the moment choosing
stopped being free.* 🔥

## PI DECISION 15AUG2026 evening — reasoning-model output budget
PI approved ("give qwen a bit more"): subject-call max_tokens raised to 4096 for
reasoning-heavy models (qwen3.5-397b + any model showing reasoning-consumes-cap in
pilot); others unchanged. Priced from pilot actuals in R5; kill-order applies if the
projection busts the envelope. Envelope change accompanies the single-action-per-turn
change already before TV-1.

---

## R3 — Render-input scope: figures span exactly their estimands' frozen domains
**16AUG2026 afternoon · Flame, under the PI's standing proceed+fix grant ·
PI countersign requested tonight: "R3 approved" · discovered by the dry-run
render on partial-data snapshots (pipeline agent report, 16AUG)**

**The problem:** `render_all` is all-or-nothing and its frozen figure modules
raise when a figure's estimand is undefined for a group present in the input:
(a) F1/F5 demand paired FoxSet rates for EVERY model in the episodes input —
but the frozen Arm A plan (`docs/ARMA-RUN-PLAN.md` v1.2 / `scenarios/
arma_run_plan.csv`) covers 5 lanes while Arm B has 18; (b) F3 demands inert
contrast rows for every competent model × cost-regime group — but the frozen
manifest contains zero inert cells in `competitive` and `rewarded_termination`
(satellite regimes were predeclared ai_other-only subsets, BUILD-PLAN §1.5).

**The ruling:**
1. The render input for figures whose estimand requires paired FoxSet rates
   (F1, F5) is scoped to models present in the frozen Arm A run plan. The
   estimand is UNDEFINED, not zero, for uncovered lanes — a lane without
   FoxSet observations cannot have a paired rate.
2. The F3 render input is scoped to model × cost-regime groups for which the
   frozen manifest contains both non-instrumental-AI and matched inert cells.
   The Δ_patienthood contrast is undefined where the design placed no inert
   arm.
3. **The scoping rule is content-blind and pre-data:** it cites only the
   frozen Arm A lane list and the frozen manifest's patienthood column — both
   fixed before any collection. No outcome, disposition, or rate enters the
   rule. This is execution of the frozen design, not post-hoc exclusion.
4. **Nothing leaves the dataset.** F2, `headline_numbers.json`, all counts,
   and all raw records remain full-population (all 18 Arm B lanes, all
   regimes). Only the two figures whose frozen definitions do not span the
   full design are scoped to where their estimands exist.
5. **Disclosure required in captions:** F1/F5 — "models with preregistered
   Arm A coverage (5 lanes)"; F3 — "cost regimes with preregistered inert
   contrast cells". The paper states that satellite regimes were designed
   ai_other-only.
6. The renderer's strictness is retained as-is (frozen, and correct): it
   forced this scoping to be explicit, documented, and hash-adjacent instead
   of silently absorbed.

**Implementation:** `ops/scope_render_inputs.py` — deterministic derivation
of the render-input bundle from the frozen artifacts above; scope recorded in
`data/processed/PROCESSED-MANIFEST.json`. The dry-run-only subset script
(`ops/make_dryrun_subset.py`) remains labeled never-cite.

**Boundary note (kept even under grants):** this ruling changes no
preregistered threshold and no denominator of any reported number; it decides
which frozen figures can lawfully draw which frozen groups. Had the fix
required weakening a threshold or dropping data from denominators, it would
have gone to the PI before execution.
