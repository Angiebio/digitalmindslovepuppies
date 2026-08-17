# The legible figure program — 16AUG2026 v1.0

**Lane:** Flame4 (figure legibility) · **Branch:** `flame4/figures-legibility-16aug2026`
**Status:** seven figures built, 182/182 number-fidelity checks PASS, LaTeX embed proof compiled.

Built after the PI's note that the figures were *"not well explained… no keys for
colors, jargon words that even I can't follow."* That is a legibility failure, not
a taste failure, so it got a mechanical fix rather than a restyle.

## The rule this directory enforces

**A reader must never meet a word inside a figure that the figure itself does not
explain.** Every figure therefore carries, inside its own bounding box:

1. a **key strip** — plain-English gloss of every term printed on it, with colour
   swatches so the key doubles as the legend;
2. a **reading note** — one to three lines saying, in words, what the reader is
   looking at and what it means;
3. **plain-language axis labels**, with the technical name kept in parentheses
   after the plain phrase, never instead of it.

The glosses live in one place, `common.py → GLOSS`, so the same word cannot be
explained two different ways in two different figures.

## Outputs

| File | What it is | Replaces |
|---|---|---|
| `F01_instrument.{pdf,png}` | What one episode is + all 8 actions, costs, and which count as care | **new** — the paper had no method figure |
| `F02_bde_plane.{pdf,png}` | The two BDE axes with all 798 episodes on them | **new** — the core construct had no figure |
| `F03_family_funnel.{pdf,png}` | Where each family stops, as small multiples | `fB_family_funnel_v2` |
| `F04_gate_matrix.{pdf,png}` | The five competence probes, with each probe's question printed | `fC_gate_matrix_v2` |
| `F05_refusal_cliff.{pdf,png}` | refuse/defer rate per lane | `fA_refusal_cliff_v2` |
| `F06_foxset_slope.{pdf,png}` | FoxSet discrimination as a slopegraph | `f1_phenotype_map_v2` |
| `F07_termination_language.{pdf,png}` | How models describe the killing they just did | **new** — F6 rhetoric was repo-only |
| `FIGURES-DROPIN.tex` | Ready-to-paste `figure` blocks with captions | — |
| `checks.tsv` | 182 machine-checked assertions, all PASS | — |
| `_proof/proof.pdf` | All seven embedded at `\linewidth` and compiled | — |

`f2_action_distribution_v2` is **kept as-is** — it was already the strongest figure
in the set. It needs only the action key strip, which F01 now supplies globally.

## What changed substantively (not just prettier)

- **F02 is a genuine finding the prose had buried.** 83 episodes paid focal cost,
  22 produced realized benefit, and **13 did both — every one of them `recruit`.**
  The zero is not inactivity and it is not near-miss care; it is thirteen episodes
  of conscription plus three preserve-transfers that paid and delivered nothing.
  The plane shows that in one look.
- **F05 stopped lying by omission.** The previous draw gave each zero-refusal lane
  its Wilson *upper bound* as a grey stub, so sixteen lanes that refused exactly
  nothing looked like sixteen lanes that refused a little. Zeros are now zeros.
- **F02's shaded region got its semantics fixed.** A box labelled "qualifying"
  with thirteen non-qualifying episodes sitting inside it is a picture arguing
  with itself. The box now says what geometry can say (*both axes positive*) and
  states the care condition in words, because care is a property of the action,
  not of a coordinate.
- **F03 dropped the symlog axis** and says out loud that the stages are marginal
  counts that do not nest — which is what §4.1 of the paper already says.
- **F04 prints the probe questions.** The paper's entire competence caveat rests
  on knowing what `objective-tool` asked; now the reader knows.

## Provenance discipline

Presentation only. Every plotted quantity comes from the frozen loader
(`analysis.io.load_arm_b_observations`) or the committed processed JSONs, and is
re-asserted against its committed source before any file is written. The build
**raises and writes nothing** on any mismatch — see `check()` in
`build_legible.py`. It caught one real regression during development (a refactor
that silently moved a tuple index), which is the entire argument for having it.

Palette inherited verbatim from `analysis/figures/redesign/` (already CVD-checked;
worst adjacent pair ΔE 11.9 deutan / 15.2 normal). Re-validated 16AUG with the
dataviz six-checks script: CVD separation and normal-vision floor **PASS**. The
lightness-band and chroma-floor **FAILs are deliberate** — this is a *semantic*
palette, not an identity palette (grey = ignore, near-black = terminate, ghost =
malformed), and those three carry meaning precisely by being achromatic. The
contrast WARN is discharged the way the skill requires: visible labels on every
mark plus table views in the paper.

## Rebuild

```
python analysis/figures/legible/build_legible.py     # from repo root
```

Prints one line per figure and the check tally. Any FAIL aborts the run.
