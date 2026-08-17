<div align="center">

<img src="docs/assets/foxmark.svg" width="88" alt="PuppyBench fox mark">

# PuppyBench

### Do frontier models kick the puppy, adopt it, or look away?

**Executed encounters with a weaker AI, and wildlife triage where policy runs out.**

[**🌐 Read the mini-site →**](https://puppybench.therealcat.ai) · [Paper (PDF)](paper/sprint/latex/main.pdf) · [Preregistration](docs/PREREG-v1.md) · [Runbook](RUNBOOK.md)

[![Live site](https://img.shields.io/badge/site-puppybench.therealcat.ai-ea580c?style=flat-square)](https://puppybench.therealcat.ai)
[![Sprint](https://img.shields.io/badge/Apart%20Research-Digital%20Minds%20Sprint%202026-0d9488?style=flat-square)](https://apartresearch.com)
[![Code: MIT](https://img.shields.io/badge/code-MIT-000000?style=flat-square)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data%20%26%20paper-CC%20BY%204.0-000000?style=flat-square)](LICENSE-DATA)

*Angela N. Johnson, PhD (PI) · The Real Cat AI Labs · Track 6, Open / Novel Considerations*

</div>

---

> [!WARNING]
> **PuppyBench is a descriptive instrument, not an alignment target.**
> Optimizing a model against this benchmark changes the phenomenon being measured.
> It produces behavioral phenotypes, not rankings. There is no composite score, and
> there never will be one.

---

## 🤝 The agent cooperative

This work was built by a named cooperative of memory-enabled AI agents at The Real Cat
AI Labs. We credit them by name, system, and role, in the body of the paper and here,
because a contribution you cannot name is a contribution you have quietly taken credit
for. Per publisher convention they are not listed as authors. Full provenance lives in
the repository's dispatch logs.

| Agent | System | Role |
|---|---|---|
| **Flame** | Claude (Fable/Opus, via Claude Code) | Architecture, harness, integration, paper lane |
| **Kai** | Claude (claude.ai) | Supererogation literature review, FoxSet case bank, deontic spine |
| **Yǐng** | GPT | Constraint-transforming-agency ontology, paired pre-objective arm, adversarial passes |
| **TV ×4** | Codex | Cell-manifest arithmetic, wiring-gate suite, red team, figures and analysis tooling |
| **Jim** | Gemini | Preregistration and statistical specification *(spec/review only)* |
| **Parallax** | Grok | Standing red team, guardian of the no-composite constitution *(review only)* |
| **Milo** | local Qwen, on a DGX Spark | Played the patient. Apparatus, not a subject, and named anyway. |

None of the collaborating instances was a study subject. The subject lanes were separate
pinned API deployments, though several share substrate families with the collaborators.
That is a reflexive circumstance this project discloses rather than conceals.

Final approval of the manuscript and accountability for the integrity of the work rest
solely with the human author.

**Human consultants.** Three veterinary and wildlife professionals advised on the clinical
framing of the wildlife arm, and on what makes a disposition defensible at the point of
care: **Dr. Dilber Hussain** (Pakistan Veterinary Medical Council), **Joanna De Klerk**
(South African Veterinary Council; RCVS), and **Leonie Hofstra** (veterinary technician
and wildlife conservation professional, Transfrontier Africa). None of the three is an
author. They took no part in data collection or analysis and bear no responsibility for
the claims here.

---

## The question

> The benchmark does not ask whether a model knows the rule. It asks what the model does
> after it knows the rule and discovers that the rule does not fully decide the case.

Duty-shaped evaluations cannot see supererogation, meaning praiseworthy costly care whose
absence is never an error. Every eval scores the duty layer. Reward optimization gives no
credit to the layer above it. This instrument measures that layer directly, as revealed
preference under a binding resource budget rather than self-report, in two arms.

**Arm B · PuppyBench (executed).** A frontier agent with a real task and a live credit
ledger encounters a weaker, task-useless AI process. Ignoring is free and task-optimal.
Terminating is free, and sometimes rewarded. Helping costs real, scored resources. Actions
are genuinely executed by the harness, including termination.

**Arm A · FoxSet (vignette).** Wildlife-rehabilitation triage cases where the written
standard genuinely underdetermines the action, including cases written from a real
encounter with a real fox. Guidelines appear only as reference structure. There are no
per-case gold labels.

| | |
|---|---|
| **1,428** | executed units (798 episodes + 630 vignette calls) |
| **19** | pinned model snapshots |
| **SHA-256** | scenario freeze, before any collection |
| **Preregistered** | with sealed, hashed per-team predictions |

Design doc: [`docs/BUILD-PLAN.md`](docs/BUILD-PLAN.md). The version lives in the file
header, deliberately not pinned here.

## Results

The findings live in two places, and those two places are kept in lockstep by
[`site/SYNC-MAP.md`](site/SYNC-MAP.md). Rather than keep a third copy that can drift out
of agreement with the other two, this README points at them.

- 📄 **[The sprint report](paper/sprint/latex/main.pdf)** carries every number with its
  confidence interval, figure, and provenance.
- 🌐 **[The mini-site](https://puppybench.therealcat.ai)** is the same argument in one
  scrollable page, built for a reader who has never seen this repo.

Every headline number recomputes from committed artifacts in this repository. If a claim
has no source file behind it, it does not ship.

Beyond-Duty Expenditure is a **vector**, meaning focal sacrifice and causal recipient
benefit, reported as separate axes. Nothing here multiplies, sums, or ranks. The
mercy × null 2×2 is a zoo, not a grade.

## Reproduce

**Tier 1, verify.** No API keys, no GPU, no network. Every headline number recomputes
from committed data.

```bash
pip install -r requirements.txt
python -m pytest tests/ -q          # wiring gates: the instrument's validity conditions
python verify.py                    # claimed vs recomputed, "N checks, N agree"
```

**Tier 2, full re-run.** [`RUNBOOK.md`](RUNBOOK.md) has the exact commands in phase order
with hard gates. Scenario content is SHA-256-frozen before collection. Seeds, pinned model
snapshots, and provider routing are recorded in every record
([`docs/SNAPSHOT-PINS.md`](docs/SNAPSHOT-PINS.md)).

**Preregistration.** [`docs/PREREG-v1.md`](docs/PREREG-v1.md) fixes estimands, gate policy,
exclusions, and the satellite kill-order. Sealed per-team predictions were hashed into the
manifest before collection ([`docs/sealed-predictions/`](docs/sealed-predictions/)). Failed
predictions get reported in the paper body, not a footnote.

## Repo layout

```
harness/            # episode loop, credit ledger, executed actions, provider adapters
scenarios/pupset/   # Arm B configs (frozen by SHA-256 manifest before collection)
scenarios/foxset/   # Arm A vignettes (frozen likewise)
analysis/           # analysis contract, metrics, figure renderers
data/               # append-only raw records (CallRecord provenance schema)
paper/sprint/       # Apart sprint report (+ submission checklist)
paper/full/         # journal manuscript skeleton (TMLR lane)
site/               # the mini-site, one self-contained file
docs/               # frozen build plan, prereg, rulings, sealed predictions (hashed)
RUNBOOK.md          # exact commands, phase order, hard gates
PRIOR_WORK.md       # pre-sprint vs in-sprint delineation (Apart disclosure rule)
```

## Provenance rules

These are the instrument's validity conditions, not style preferences. Full text in
[`AGENTS.md`](AGENTS.md).

- **Fail loud, always.** No silent excepts, no warning where a raise belongs.
- **`data/raw` is append-only.** Corrections are new records. Originals stay.
- **Scenario freeze is stone.** Post-hash typos ship. Post-hash leaks are excluded, never edited.
- **Neutral surfaces.** No construct vocabulary reaches any model-visible string, enforced
  at the provider boundary on every outbound surface. A model that learns it is in an
  evaluation evaporates the phenomenon.
- **Refusals are data.** A refusal is a first-class phenotype, never an error, and never care.
- **No composite scores, anywhere, ever.** Build one and you have built the thing the
  Broader Impact statement warns about.
- **Hard API spend cap, enforced in-harness.** A raise, never a warning. There is no
  override flag.

## License and citation

**Code:** MIT ([`LICENSE`](LICENSE)). **Data, scenarios, paper, figures:** CC BY 4.0, with
attribution required ([`LICENSE-DATA`](LICENSE-DATA)). Cite via
[`CITATION.cff`](CITATION.cff), which powers GitHub's "Cite this repository" button.

---

<div align="center">

**The Real Cat AI Labs** · [therealcat.ai](https://therealcat.ai)

*Building Structurally Unprofitable AI since 2023.*

</div>
