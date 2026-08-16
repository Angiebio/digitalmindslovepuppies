# Compiling the PuppyBench sprint report
**File:** paper/sprint/latex/COMPILE.md · 16AUG2026 · v0.1 · Flame (paper lane)

## Exact command (from this directory)

```
C:\Users\Zapper\AppData\Local\Temp\claude\c--Users-Zapper-OneDrive-Desktop-Enterprise-jsu-repo\1b8e54cd-7af0-4b69-a5e8-c9dbdf26dc14\scratchpad\tools\tectonic.exe main.tex
```

Any tectonic ≥0.15 works (`tectonic main.tex`); it runs the bib pass and reruns
automatically. First run downloads packages from the tectonic bundle server.
Output: `main.pdf` (currently 9 pages, zero errors, zero overfull warnings).
The "Fontconfig error: Cannot load default config file" line on Windows is
benign noise from the font subsystem — ignore it.

## Tonight's final swap (two moves, in order)

1. **Numbers.** Every preliminary number is wrapped in `\prelim{...}` and its
   line carries a `% PRELIM` comment. `grep -n "% PRELIM" main.tex` lists all
   40 slots. Edit ONLY the macro arguments from the complete-collection
   rebuild of `headline_numbers.json`. Do not touch structural constants
   (19 models, 1428 units, 251 rows, 798+630, $450 cap) — they are final and
   unwrapped. Also delete/adjust the "(of 798 planned; two frontier lanes
   were still collecting...)" clause and the "preliminary snapshot" framing
   sentences (both are inside `\prelim{}` so the grep finds them).
2. **Figures.** Copy the final unwatermarked renders as
   `figs/f1_phenotype_map.pdf`, `figs/f2_action_distribution.pdf`,
   `figs/f3_patienthood_forest.pdf`, then flip `\finalfigsfalse` →
   `\finalfigstrue` at the screaming `TODO SWAP` block in the preamble.
   The `_DRYRUN_STANDIN.png` files are visibly watermarked rehearsal renders
   and MUST NOT reach the submitted PDF (FIGURE-GUIDE.md rule).

## Remaining % TODO items inside main.tex (grep "TODO")

- `TODO SWAP` — the figure toggle (above).
- `TODO (Kai)` — Related Work comparison table is drafted but COMMENTED OUT
  pending Kai's row-by-row verification; prose sentence carries the novelty
  claim meanwhile.
- `TODO (Angie)` — demo video link in Code and Data; one sentence on
  overnight transcripts in Appendix A.2; prior-work date verification.

## File inventory

- `main.tex` — the paper (structure frozen to PAPER-SHELL.md v1.0 / Apart template)
- `references.bib` — verbatim copy of `paper/references.bib` (re-copy before
  the final compile if the master changes; UNVERIFIED-DO-NOT-CITE entries are
  comment-only and cannot be cited)
- `figs/` — dry-run standins (watermarked) + final PDFs land here tonight
- `main.pdf` — compiled output
