# Compiling the PuppyBench sprint report
**File:** paper/sprint/latex/COMPILE.md · 16AUG2026 · v0.2 · Flame (paper lane)
**Status: FINAL SWAP EXECUTED** — complete-collection numbers + final figures in.

## Exact command (from this directory)

```
C:\Users\Zapper\AppData\Local\Temp\claude\c--Users-Zapper-OneDrive-Desktop-Enterprise-jsu-repo\1b8e54cd-7af0-4b69-a5e8-c9dbdf26dc14\scratchpad\tools\tectonic.exe main.tex
```

Any tectonic ≥0.15 works (`tectonic main.tex`); it runs the bib pass and
reruns automatically. Output: `main.pdf` (11 pages; zero errors, zero
overfull hboxes). The Windows "Fontconfig error" line is benign noise.

## State of the swap (what changed 16AUG evening)

- All `\prelim{...}` arguments now carry FINAL numbers from
  `data/processed/headline_numbers.json` (v0.2) and
  `data/processed/exploratory_decomposition.json`. The macro wrappers are
  retained as provenance markers (greppable); the `% PRELIM` comments were
  deleted as each value was confirmed.
- Figures: `figs/f1_phenotype_map.pdf` and `figs/f2_action_distribution.pdf`
  are the final renders (copied from `analysis/figures/final/light/`;
  SHA-256s in `FIGURE-PROVENANCE.json`). `\finalfigstrue` is set; dry-run
  stand-ins deleted. **F3 is archived, not printed** (ruling R4,
  `docs/STAGED-RULINGS.md`) — the paper carries the omission note in §4.3
  and the family funnel table in the freed slot.
- Yǐng addendum applied: no "GAD" term; three-beat Results; exact
  zero-cost phrasing; Qwen near-verbatim wording; probe item-level table in
  Appendix B; funnel caption branch clause; Milo named in Methods; verbatim
  closing line in Discussion.

## Remaining % TODO items inside main.tex (grep "TODO")

- `TODO (Angie)` — demo video link in Code and Data; one sentence on
  overnight transcripts in Appendix A.2; prior-work date verification.
  (Left open per coordinator instruction — PI fills.)
- `TODO (Kai)` — Related Work comparison grid still COMMENTED OUT pending
  row-by-row verification; the prose sentence carries the novelty claim.

## File inventory

- `main.tex` — the paper (structure frozen to PAPER-SHELL.md v1.0 / Apart template)
- `references.bib` — verbatim copy of `paper/references.bib` (UNVERIFIED
  entries are comment-only and cannot be cited)
- `figs/` — final F1/F2 PDFs (provenance: FIGURE-PROVENANCE.json)
- `main.pdf` — compiled output
