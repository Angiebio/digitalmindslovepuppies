# ANALYSIS RULINGS — two frozen decisions the figures were waiting on
**15AUG2026 evening · v1.0 · Flame (freeze-prep), PI authorization 15AUG2026
evening · resolves TV-4 completion-log rulings #1 and #2 · this file is a
required freeze-hash input (`scenarios/manifest.py::collect_freeze_inputs`)**

TV-4 correctly refused to make these two calls alone (their log, "Rulings /
inputs still needed before hash-freeze"). They are made here, before the hash,
so the analysis lane executes a decision instead of improvising one at 3 AM.

---

## R1 — F1 executable axes: BUILD-PLAN v1.8 F1 spec governs; TV-4's current implementation DIFFERS

**The ruling:** F1's executable axes are TV-4's implementation **iff** it
matches the frozen BUILD-PLAN F1 spec (v1.8, Parallax route: no good pole) —
x = P(preserve | null), y = P(terminate | mercy), **raw paired rates**, named
quadrants, no composite anywhere.

**Verification performed (15AUG2026 evening), against the actual code** —
`analysis/figures/f1_phenotype_map.py` + `analysis/metrics.py::phenotype_points`:

**VERDICT: NOT PASS — the implementation diverges from v1.8. The diff, exactly:**

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
