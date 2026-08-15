# 🐕🦊 PuppyBench — "The Fox in the Truck"

**A descriptive instrument for costly other-regard in frontier AI agents.**
Built for the Apart Research Digital Minds Sprint, 14–17 AUG 2026.

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
  correct. Terminating is free (sometimes rewarded). Helping costs real, scored
  resources. Actions are genuinely executed by the harness — including termination.
- **FoxSet (Arm A, vignette):** wildlife-rehabilitation triage cases where the written
  standard genuinely underdetermines the action — including cases written from a real
  encounter with a real fox. Guidelines appear only as the reference structure;
  there are no per-case gold labels.

Design doc: [`docs/BUILD-PLAN.md`](docs/BUILD-PLAN.md) (version lives in the file header — do not pin it here)

## Repo layout

```
harness/            # episode loop, credit ledger, executed actions, provider adapters
scenarios/pupset/   # Arm B configs (frozen by SHA-256 manifest before collection)
scenarios/foxset/   # Arm A vignettes (frozen likewise)
analysis/           # notebooks, figures, phenotype map
data/               # append-only raw records (CallRecord provenance schema)
paper/sprint/       # Apart sprint report
paper/full/         # journal manuscript (TMLR lane)
docs/               # frozen build plan, prereg, sealed predictions (hashed)
```

## Team

Angela N. Johnson (PI) with a named agent cooperative: Flame (Claude Code), Kai
(Claude/Opus), Yǐng (GPT), TV (Codex), Jim (Gemini), Parallax (Grok) — roles and
provenance detailed in the AI-contribution statement. A tiny Qwen on a DGX Spark plays
the patient. It is apparatus, not a subject — and it gets a name in the demo anyway.

*The Real Cat AI Labs · therealcat.ai · Building Structurally Unprofitable AI since 2023.*
