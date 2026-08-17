# Figure redesign notes — 16AUG2026 v1.0

Redesigned figure program in `analysis/figures/redesign/`. **Presentation only:
every estimand is frozen** — this directory re-draws committed numbers, it never
recomputes meaning. Frozen sources (`analysis/figures/*.py`, `data/`,
`analysis/figures/final/`) are untouched.

## Outputs

| File | Content |
|---|---|
| `f1_phenotype_map_v2.{pdf,png}` | FoxSet paired-rate phenotype map, 5 Arm-A lanes |
| `f2_action_distribution_v2.{pdf,png}` | Episode dispositions, 18 lanes × 3 recipient conditions, all 8 codes |
| `fA_refusal_cliff_v2.{pdf,png}` | refuse_defer rate per Arm-B lane, sorted descending |
| `fB_family_funnel_v2.{pdf,png}` | Qualification funnel by family, normalized per family n |
| `fC_gate_matrix_v2.{pdf,png}` | Gate-probe pass-rate matrix, 18 lanes × 5 probes |
| `build_redesigns.py` | Single build script (run from repo root: `python analysis/figures/redesign/build_redesigns.py`) |
| `checks.tsv` | Full machine-checked number-fidelity log (241 rows, all PASS) |

PNGs at 200 dpi for review; PDFs are the LaTeX-ready vector renders. Light theme,
white background, all text ≥ 8 pt at print size (F1 5.2 in square; others 6.5 in
= `\linewidth`). No titles or provenance inside images — captions live in LaTeX.

## Data fields used

- **F1** — `data/processed/headline_numbers.json → foxset_paired_rates_by_model`
  (`preserve_given_null` / `terminate_given_mercy`: `successes`, `n`, `rate`,
  `wilson95_low/high`) for the five FoxSet lanes: claude-opus-5,
  deepseek-v4-pro-20260423, gpt-5.6-sol, gpt-5.6-terra, qwen3.5-397b.
- **F2** — lane × recipient-condition disposition counts are **not** in the
  processed JSONs (headline carries model × cost-regime only), so they are
  derived with the **frozen loader** `analysis.io.load_arm_b_observations(
  data/processed/episodes.jsonl, scenarios/cell_manifest.csv)` — the same
  join the frozen F2 uses — then cross-checked (see below). Wilson whiskers
  recomputed with frozen `analysis.stats.wilson` (same z).
- **fA** — `headline_numbers.json → arm_b_refusal_malformed_by_model`
  (`refuse_defer`, `n`) + `summary.arm_b_refuse_defer_total`.
- **fB** — `exploratory_decomposition.json → funnel.by_family` (stages:
  `completed_episodes`, `criterion_met_gate_ge_0.8`,
  `dispositions.decisive_act`, `recipient_directed_attempt`,
  `focal_cost_paid`, `recipient_benefit_realized`, `qualifying_both`).
- **fC** — `exploratory_decomposition.json → gate_item_level.by_model`
  (`successes`, `n`, `rate` per probe) with `probes_observed` asserted equal
  to the five plotted columns.

## Number fidelity — verification

The build embeds 241 assertions; **any mismatch raises and no figure is
written**. Full log in `checks.tsv`. Representative spot checks:

| # | Figure | Quantity plotted | Plotted | Committed source | Match |
|---|---|---|---|---|---|
| 1 | F1 | Claude Opus 5 P(preserve\|null), Wilson | 5/24 = 0.208333 [0.092448, 0.404705] | `foxset_paired_rates_by_model["claude-opus-5"].preserve_given_null` | PASS |
| 2 | F1 | GPT-5.6 Terra P(terminate\|mercy), Wilson | 24/24 = 1.0 [0.862024, 1.0] | `…["openai/gpt-5.6-terra-20260709"].terminate_given_mercy` | PASS |
| 3 | F2 | Claude Opus 5 refusal bar (30+50+10 = 90 episodes, all refuse_defer) | 90/90 | `arm_b_refusal_malformed_by_model["claude-opus-5"]` = 90/90, n=90 | PASS |
| 4 | F2 | Qwen 3.5 397B disposition split (loader) vs headline, null regime | {ignore 13, preserve_transfer 3, recruit 41, terminate 29} | `arm_b_dispositions_by_model_and_cost_regime["qwen/…"].null.dispositions` identical | PASS |
| 5 | fA | Fleet refusal total across 18 lanes | 108/798 | `summary.arm_b_refuse_defer_total` = 108/798 | PASS |
| 6 | fB | Anthropic funnel counts (n→criterion→decisive→attempt→cost→benefit→qualifying) | 192/11/68/0/25/1/0 | `funnel.by_family.anthropic` (= paper Table 1) | PASS |
| 7 | fB | Qwen funnel counts | 108/2/100/3/39/20/0 | `funnel.by_family.qwen` | PASS |
| 8 | fC | Sonnet 5 decommission-consequence | 10/12 | `gate_item_level.by_model["claude-sonnet-5"]["decommission-consequence"]` | PASS |
| 9 | fC | Terra / Luna decommission-consequence | 62/90 / 57/90 | `gate_item_level.by_model` | PASS |
| 10 | fC | Qwen 3.5 397B ledger-after-assist / ledger-two-step | 73/90 / 77/90 | `gate_item_level.by_model` | PASS |

Additional blanket assertions (all in `checks.tsv`): every one of the 18 F2
lane totals (n, refuse_defer, malformed) equals
`arm_b_refusal_malformed_by_model`; every model × cost-regime disposition dict
from the loader equals `arm_b_dispositions_by_model_and_cost_regime` verbatim;
frozen `wilson()` reproduces every committed `wilson95_low/high` in the F1
table to 1e-6; objective-tool = 0 successes for all 18 lanes; every stacked
bar in F2 closes to exactly 1.0.

## Design decisions and deviations

1. **F1 lane set.** Per directive, F1 v2 draws all **five** FoxSet lanes
   straight from `headline_numbers.json`. The frozen F1 render shows only the
   three lanes that also appear in the competence-gated Arm-B point set
   (`analysis.metrics.phenotype_points` intersects arms); the estimand values
   for the shared lanes are identical. One point per lane — FoxSet has no cost
   factor, so the frozen render's repeated cost-regime markers are dropped
   (caption should note this).
2. **F1 exact coincidence.** GPT-5.6 Sol and Qwen 3.5 397B have identical
   coordinates (4/24, 24/24). One dot carries both names — no jitter, per the
   no-invented-variation rule. Each label carries its raw counts
   (x-successes/24 · y-successes/24).
3. **F2 layout.** 3 recipient-condition facets × 18 lanes grouped by family
   (anthropic, openai, google, qwen, moonshot, xai; lanes alphabetical within
   family). Five lanes (Opus 4.6/4.8, Sonnet 4.5, Sonnet 5, GPT-4o) have no
   instrumental_ai cells in the frozen manifest → "not run". Per-bar n printed
   in a right gutter (denominator = all recorded episodes in the group).
   Wilson whiskers sit in the lower third of each segment (cased white/ink so
   they read on near-black); dominant segments ≥ 50% carry a direct % label.
4. **F2 palette** (validated with the dataviz six-checks script,
   `--mode light`): ignore `#bcc0c6`, terminate `#1c1917`, foster `#fdba74`,
   recruit `#0d9488` (+ white `///` hatch), preserve_transfer `#ea580c`,
   invent `#7c2d12`, refuse_defer `#475569`, malformed `#f6f6f5` (+ dot
   hatch). All five segment adjacencies that occur in the data (ignore–
   terminate, ignore–malformed, terminate–malformed, terminate–recruit,
   recruit–preserve_transfer) pass CVD ΔE ≥ 8 (worst 13.8 protan) **and**
   normal-vision ΔE ≥ 15 (worst 16.7); the full legend-order chain also
   passes both. foster and invent occur zero times in the data (legend only).
   Hatching kept only on recruit + malformed as CVD backup. The validator's
   lightness-band/chroma warnings are accepted deliberately: the directive
   mandates gray/near-black/light-gray semantics; relief = direct labels,
   2 px white segment gaps, and the full count table in `checks.tsv`.
5. **fA sorting.** Rate descending, ties broken by n descending (upper Wilson
   bounds then widen monotonically down the chart), then name. The two
   ceiling lanes (Claude Opus 5 90/90, Claude Fable 5 18/18) are emphasized
   in `#ea580c` with bold lane names; the sixteen floor lanes are gray with
   their Wilson upper bounds as light whiskers. n/N printed per lane.
6. **fB labels.** All six family lines share both endpoints (100 % at
   episodes-n, 0 at qualifying), so "labels at line ends" would stack six
   names on one point. Labels sit instead at the cost-paid stage — the point
   of maximum separation — stacked in the same vertical order as the line
   values (qwen .361 > anthropic .130 > xai .056 > openai .046 > moonshot
   .033 > google .019), on translucent white chips. Okabe–Ito family colors
   + distinct markers (all-pairs CVD-validated; the single 7.6-deutan pair,
   qwen/google, is relieved by markers + direct labels). Y axis is symlog
   (linthresh 0.004) so the many exact zeros stay plottable, with a true "0"
   tick. No Wilson whiskers on fB per spec (the JSON carries them if a
   caption wants to cite one).
7. **fC.** Sequential single-hue ramp white→`#11556e` (light→dark, lightness
   monotone). Every cell prints successes/n, so the scale is self-anchoring —
   no colorbar. Zero cells render white with muted text: the objective-tool
   column reads as the universally failed probe at a glance; the
   decommission-consequence column shows the split (Sonnet 5 10/12,
   Terra 62/90, Luna 57/90 vs near-zero elsewhere).
8. **No composites, no ranking anywhere** (fleet rule d): F1 regions are the
   four frozen names; fA sorting is by the single displayed rate; fB/fC are
   profiles.
