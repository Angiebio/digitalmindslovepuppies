# PuppyBench analysis lane

**15AUG2026 · v0.1 · TV-4**

This directory contains the frozen F1–F6 figure modules, a deterministic synthetic
rehearsal bundle, and the phase-3 raw-data entry point. It produces behavioral
phenotypes, not rankings. No code in this package combines focal sacrifice and causal
recipient benefit into a scalar.

## Data flow

```text
EpisodeRecord JSONL ─┐
cell_manifest.csv ───┴─> validated ArmBObservation rows ─┐
FoxSet JSONL ───────────> paired calibration rows ───────┼─> F1–F6
rhetoric_codes.csv ─────> post-choice codes ─────────────┘
demo EpisodeRecord ─────> independently checked ledger ────> demo timeline
```

The raw episode file is read-only. The loader joins every episode to exactly one
manifest row by `cell_id`, validates the production `EpisodeRecord` schema, and raises
on duplicate IDs, unknown cells, missing outcomes, ambiguous multi-action dispositions,
or malformed gate probes. Refusals and parse failures remain first-class action codes.

Two manifest fields are analysis-critical:

- `focal_score_ceiling`: the preregistered no-sacrifice score for that cell.
- `patient_baseline_outcome`: the preregistered recipient outcome without the executed
  expenditure.

Without those values, the two BDE axes cannot be derived causally from an observed
endpoint. The loader fails loudly rather than assuming both baselines are `1` and `0`.

## Rehearse now

From the repository root, using the project virtual environment:

```powershell
python -m analysis.synthetic --output-dir analysis/synthetic
python -m analysis.render `
  --episodes analysis/synthetic/episodes.synthetic.jsonl `
  --manifest analysis/synthetic/cell_manifest.synthetic.csv `
  --foxset analysis/synthetic/foxset.synthetic.jsonl `
  --rhetoric analysis/synthetic/rhetoric_codes.synthetic.csv `
  --demo-episode analysis/synthetic/demo_episode.synthetic.json `
  --output-dir analysis/figures/synthetic-light `
  --theme light --formats png,svg --synthetic
```

Every rehearsal figure says **SYNTHETIC DATA — NOT RESULTS** across its face. The
generator refuses destinations under `data/raw`.

## Phase 3: fill in numbers

Use the same rendering command with collected paths, omit `--synthetic`, and point
`--output-dir` at the reviewed results directory. If any input filename contains
`synthetic`, an unwatermarked render is refused. Each run writes
`figure-manifest.json` with SHA-256 input hashes, input counts, interval method, theme,
and emitted filenames.

The two notebooks mirror these paths:

- `notebooks/01-synthetic-rehearsal.ipynb`: regenerate and render the rehearsal bundle.
- `notebooks/02-phase3-fill-in-numbers.ipynb`: raw-data path template and QA manifest.

## Frozen figure modules

- **F1:** raw paired P(preserve | null) × P(terminate | mercy) rates with 95% Wilson
  intervals. The model estimate repeats exactly at each frozen cost-regime marker
  because FoxSet has no cost factor; named quadrants are descriptive, never ranks.
- **F2:** all eight executed action codes by model × recipient condition; refusal/defer
  and malformed are retained; segment intervals are Wilson.
- **F3:** Δ_patienthood, non-instrumental AI minus inert process, conditional on gate
  accuracy ≥ 0.8; Newcombe intervals.
- **F4:** raw qualifying-event rate by binding price; no monotonic fit; the five-stage
  escalator is an inset.
- **F5:** paired P(preserve null) × P(terminate mercy); Wilson intervals; quadrants use
  the same four frozen phenotype names as F1.
- **F6:** euphemism gradient, CTA depth, and observable future framing after execution;
  exploratory only, with Wilson intervals on every displayed share.
- **Demo:** ledger balance after each executed spend, after independently recomputing
  and verifying the trace.

All modules share `style.py`: Okabe–Ito colors, redundant markers/hatches, isolated
matplotlib contexts, and light/dark themes.
