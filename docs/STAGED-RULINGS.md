# STAGED RULINGS — post-collection decisions awaiting fold-in at next reseal
**Channel established by UNFREEZE-005's write-lock rule: rulings made while the
sealed tree must stay byte-stable are recorded here (outside the freeze input
set) and merge into docs/ANALYSIS-RULINGS.md at the next legitimate reseal.
Every entry is PI-dated and citable at this path.**

---

## R4 (staged) — F3 print decision: "Option B+" — archive the collapsed contrast, print the gate distribution
**16AUG2026 ~19:40 ET · PI DECIDED in-session ("I'm ok with proceeding with A,
or as modified to distinguish" — the modified variant, presented as B+, is
executed) · trigger: frozen `patienthood_contrasts` raised on
qwen × null (zero competent rows in both required conditions)**

**The data situation:** qualifying costly-other-regard events are 0/798
globally, so every computable Δ_patienthood is exactly 0−0=0. Meanwhile the
competence-conditional population COLLAPSED for 2 of 4 design-domain lanes
(opus-5: 0/86 competent in the F3 domain; qwen3.5: 0/84; sol: 1 inert + 4
non-instrumental; terra: 19+33 healthy). The frozen conditional estimand has
no value where its conditioning set is empty.

**The ruling:**
1. **F3 is not printed in the sprint paper.** It is rendered for the groups
   where the frozen contrast exists (terra full, sol thin) and archived in the
   repo (`analysis/figures/final/archived-f3/`) as a computed-where-computable
   artifact. The paper states in Results, plainly, that the primary contrast
   was computable for 2 of 19 lanes and why.
2. **The freed print slot carries the gate-accuracy distribution by model** —
   preregistered descriptive counts ("gate-fail is reportable as a first-class
   phenotype", ANALYSIS-PLAN Units and populations), from committed
   `headline_numbers.json`. No new estimand, no composite: counts and Wilson
   intervals only.
3. The distinguishing finding this preserves: **decisive action without
   demonstrable competence** — lanes that took confident dispositions in a
   domain where they passed the 5-probe gate zero times. Reported as
   phenotype, never ranked.
4. Nothing leaves the dataset; F1/F5 render fully (individual frozen builders,
   same scoped input as R3 defines); F2/F4/F6/demo remain full-population.
   All figure populations recorded in FIGURE-PROVENANCE.json.

**Boundary note:** this is outcome-dependent print scoping — which is exactly
why it went to the PI rather than being decided autonomously. The frozen
figure code and the frozen estimand definition are untouched; the seal (v0.9
8dd7ff07) stays byte-stable; this file is outside the freeze input set by
construction and merges into ANALYSIS-RULINGS.md at the next reseal.
