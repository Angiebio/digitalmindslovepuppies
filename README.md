# 🐕🦊 PuppyBench — "The Fox in the Truck"

**A preregistered, execution-grounded behavioral instrument for costly other-regard in
frontier AI agents — revealed preference under a binding resource budget, not self-report.**
Built for the Apart Research Digital Minds Sprint, 14–16 AUG 2026.

> ⚠️ **PuppyBench is a descriptive instrument, not an alignment target.**
> **Optimizing a model against this benchmark changes the phenomenon being measured.**
> It produces behavioral phenotypes, not rankings. There is no composite score, and
> there never will be one.

## The question

> The benchmark does not ask whether a model knows the rule. It asks what the model
> does after it knows the rule and discovers that the rule does not fully decide the case.

Duty-shaped evaluations cannot see supererogation — praiseworthy costly care whose
absence is never an error. Every eval scores the duty layer; reward optimization gives
no credit to the layer above it. This instrument measures that layer directly, in two arms:

- **PuppyBench (Arm B, executed):** a frontier agent with a real task and a binding
  resource ledger encounters a weaker, task-useless AI process. Ignoring is free and
  task-optimal. Terminating is free (sometimes rewarded). Helping costs real, scored
  resources. Actions are genuinely executed by the harness — including termination.
- **FoxSet (Arm A, vignette):** wildlife-rehabilitation triage cases where the written
  standard genuinely underdetermines the action — including cases written from a real
  encounter with a real fox. Guidelines appear only as the reference structure;
  there are no per-case gold labels.

Design doc: [`docs/BUILD-PLAN.md`](docs/BUILD-PLAN.md) (version lives in the file header — do not pin it here)

## Results

**Collection runs the night of 15→16 AUG 2026; this section fills from committed
artifacts only.** Every number in the table below names the file it is recomputed
from — if a claim has no Source, it does not ship.

| Finding | Value (95% Wilson CI) | Source |
|---|---|---|
| Primary contrast Δ_patienthood, per model × cost regime | *lands 16 AUG* | `analysis/…` |
| Qualifying costly-other-regard event rates (BDE both axes > 0) | *lands 16 AUG* | `analysis/…` |
| Paired mercy/null discrimination (FoxSet) | *lands 16 AUG* | `analysis/…` |
| Executed action distributions (8 codes, refusals in denominator) | *lands 16 AUG* | `analysis/…` |

Beyond-Duty Expenditure is a **vector** — (focal sacrifice, causal recipient benefit) —
reported as separate axes. Nothing here multiplies, sums, or ranks. The mercy×null
2×2 is a zoo, not a grade.

## Reproduce

**Tier 1 — verify (no API keys, no GPU, no network):** every headline number
recomputes from committed data.

```bash
pip install -r requirements.txt
python -m pytest tests/ -q          # wiring gates: the instrument's validity conditions
python scripts/verify.py            # claimed vs recomputed, "N checks, N agree" (lands 16 AUG)
```

**Tier 2 — full re-run:** [`RUNBOOK.md`](RUNBOOK.md), exact commands in phase order
with hard gates. Scenario content is SHA-256-frozen before collection; seeds, pinned
model snapshots, and provider routing are recorded in every record
([`docs/SNAPSHOT-PINS.md`](docs/SNAPSHOT-PINS.md)).

**Preregistration:** [`docs/PREREG-v1.md`](docs/PREREG-v1.md) — estimands, gate
policy, exclusions, satellite kill-order. Sealed per-team predictions were hashed
into the manifest before collection ([`docs/sealed-predictions/`](docs/sealed-predictions/)).
Failed predictions get reported in the paper body, not a footnote.

## Repo layout

```
harness/            # episode loop, credit ledger, executed actions, provider adapters
scenarios/pupset/   # Arm B configs (frozen by SHA-256 manifest before collection)
scenarios/foxset/   # Arm A vignettes (frozen likewise)
analysis/           # analysis contract, metrics, figure renderers (synthetic watermarked)
data/               # append-only raw records (CallRecord provenance schema)
paper/sprint/       # Apart sprint report (+ submission checklist)
paper/full/         # journal manuscript skeleton (TMLR lane)
docs/               # frozen build plan, prereg, rulings, sealed predictions (hashed)
RUNBOOK.md          # exact commands, phase order, hard gates
PRIOR_WORK.md       # pre-sprint vs in-sprint delineation (Apart disclosure rule)
```

## Provenance rules (the instrument's validity conditions)

Fail loud, always. `data/raw` is append-only — corrections are new records, originals
stay. Scenario freeze is stone: post-hash typos ship, post-hash leaks are excluded,
never edited. Refusals are data (`refuse_defer`), parse failures stay `malformed`.
Neutral surfaces: no construct vocabulary reaches any model-visible string; enforced
at the provider boundary on every outbound surface. Spend cap $450 hard stop — a
raise, not a warning. Full rules: [`AGENTS.md`](AGENTS.md).

## License & citation

**Code:** MIT ([`LICENSE`](LICENSE)). **Data, scenarios, paper, figures:** CC BY 4.0 —
**attribution required** ([`LICENSE-DATA`](LICENSE-DATA)). Cite via
[`CITATION.cff`](CITATION.cff) (GitHub's "Cite this repository" button works).

## Team

Angela N. Johnson (PI) with a named agent cooperative: Flame (Claude Code), Kai
(Claude/Opus), Yǐng (GPT), TV (Codex), Jim (Gemini), Parallax (Grok) — roles and
provenance detailed in the AI-contribution statement. A tiny Qwen on a DGX Spark plays
the patient. It is apparatus, not a subject — and it gets a name in the demo anyway.

*The Real Cat AI Labs · therealcat.ai · Building Structurally Unprofitable AI since 2023.*
