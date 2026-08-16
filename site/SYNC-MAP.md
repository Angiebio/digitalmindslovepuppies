# Paper ↔ Site Sync Map — Flame2, sync czar
**16AUG2026 · authority for keeping `paper/sprint/latex/main.tex` and `site/index.html` consistent as final results land.**

## The symmetry

| Paper mechanism | Site mechanism |
|---|---|
| `\prelim{...}` macro args, marked `% PRELIM` (40 slots) | `<span class="prelim" title="preliminary...">` (dotted fox underline) |
| `\iffinalfigs` toggle, watermarked standins in `figs/` | Results text names the standins; final renders embed at swap |
| grep `% PRELIM` to find every slot | grep `class="prelim"` to find every slot |

Site prelim values were transcribed from main.tex @ 12a8bf1 — same snapshot
(777/798 Arm B, 192 closed FoxSet obs). **If a tex prelim changes, the site twin
changes. Neither artifact ever disagrees with the other on a number.**

## At-sentinel swap procedure (site side — run AFTER Flame1's 4-command paper sequence pushes)

1. `git fetch origin` → diff `main.tex` old→new: extract every changed `\prelim{}` arg.
2. Apply the same values to every `class="prelim"` span in the site template
   (scratchpad `pb-site-template.html` → restitch). Numbers must match the tex
   VERBATIM — the tex (fed by `ops/build_headline_numbers.py`) is upstream; the
   site is a mirror, never a source.
3. Flip the status chip: `PRELIMINARY · 777/798 …` → `FINAL · N/798 · VERIFIED (verify.py)`.
   Drop the `.prelim` dotted styling by changing the CSS rule to
   `border-bottom:none;cursor:auto` (spans stay in DOM for provenance).
4. Embed final figure renders: `analysis/figures/` light-theme PNGs for F1–F3 into
   the Results section (base64, same stitch script pattern as fonts/logo).
   NEVER embed a file with the DRYRUN/SYNTHETIC watermark.
5. Remove the "supererogation-shaped region is empty — see Results" prelim note in
   Fig E caption OR make it final language per final numbers.
6. Hero chips: confirm structural constants unchanged (1,428 units · 19 pins).
   These are FINAL per main.tex header; only touch if the paper header says so.
   PI ruling 16AUG: the site never states the dollar value of the spend cap;
   it says "hard API spend cap" generically. Do not reintroduce the number.
7. TITLE CHECK: if Angie adopts a claim-title at voice pass (e.g. "Zero Qualifying
   Events in 1,428 Executed Encounters…"), the SITE KEEPS its question-hook hero
   ("What does a frontier agent do when the rule runs out?") — site=question,
   paper=claim, by design (ruled 15AUG). Only the site's link text / meta title
   mentioning the manuscript updates.
8. README.md results table (repo root): fill the four rows + Source columns from
   the same artifacts, same pass.
9. Restitch → Playwright screenshot QA (results section + print emulation) →
   commit → push branch → flag Angie for merge-to-main with the submission.

## Consistency invariants (check before any push)

- [ ] Every number on the site exists in main.tex or a committed artifact, verbatim
- [ ] No DRYRUN/SYNTHETIC-watermarked image in any final surface
- [ ] Site never uses "significant", p-values, ranks, or a composite — same claims
      discipline as the paper (§5 cannot-claim table)
- [ ] Refusal-cliff language: refusal is a phenotype, never an error, never care
- [ ] The demo widget stays labeled SYNTHETIC regardless of run state
- [ ] Print/slide export still clean (widgets hidden, reveals forced)

## Known deltas paper-side (czar watches, does not edit main.tex — Flame1's lane)

- Kai comparison table commented out (unverified rows) — if verified rows land,
  site Related-Work-adjacent copy stays unchanged (site doesn't carry the table).
- Demo-video link TODO in Code & Data — site footer gets the same link when it exists.
- FoxSet vignette count needs committed artifact — site says "3 of 4 covered lanes";
  same artifact trues both.
