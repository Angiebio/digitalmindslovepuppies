# PuppyBench Sprint Report — SHELL v1.0
**File:** paper/sprint/PAPER-SHELL.md · **Date:** 15AUG2026 · **Author:** Flame#2 (paper lane)
**Status:** structure FROZEN to the official Apart template; prose slots pre-drafted from
BUILD-PLAN v1.7 §0/§4-Phase-4 + ANALYSIS-PLAN v0.2. Numbers land Sunday from `analysis/`.
**Every ⟨FILL⟩ slot names its source.** No number enters this document except from a
committed artifact — the README's Source-column rule applies to the paper too.

---

## HOW TO USE THIS SHELL (Sunday workflow)

1. Copy the official Apart template Google Doc (link in SUBMISSION-CHECKLIST.md — use
   the Guidelines-tab copy, NOT any email copy; they can be stale).
2. Paste each section below into the matching template section. The template order is
   EXACTLY the order here. Delete the slot annotations as you fill them.
3. Page budget (template's own guidance, 4 pages excluding references + appendix):
   Intro & Related Work ~1p · Methods + Results ~2.5p · Discussion ~0.5p.
4. Abstract: **≤150 words** (the page cap; the doc says 150–250 — take the safer cap).
5. Export PDF. The PDF is the judged artifact; the repo is supporting evidence.
6. Resubmission before deadline is allowed with the exact same title — files replace.

**Rubric we are writing against (3 dimensions, 1–5 each):**
- D1 Impact/Innovation — 4 = "identifies a neglected problem area"; 5 = "opens a new
  research direction. Clear theory of change." Our framing must say both, plainly.
- D2 Execution — 4–5 = validation, robustness, honest limitations. The wiring gates,
  prereg, frozen manifest, and exact CIs are the evidence. Cite them in Methods.
- D3 Clarity — "diluted by excessive length" is a scoring penalty. 4 pages. Cut.

---

# TITLE

**WORKING TITLE (submit-safe even if no single headline crystallizes):**

**Duty-Shaped Evaluations Cannot See Costly Care:
PuppyBench, an Executed Measure of Beyond-Duty Expenditure in Frontier AI Agents**

Rationale: prior winners' titles are CLAIMS, not project names — and this claim is
defensible from construction alone, so it survives ANY result including a null
Δ_patienthood (a null is a finding: generalized repair reflex). "Executed,"
"measure," and the construct name all signal method in the title line.

*(Title footnote, required by template: "Research conducted at the Digital Minds
Research Sprint, August 2026.")*

⟨SUNDAY RETITLE — if F1/F3 deliver a crisp phenotype sentence, promote it:
- "⟨Finding⟩: Executed Measurement of Costly Other-Regard in ⟨N⟩ Frontier Agents"
  e.g. "Frontier Agents Diverge Where Helping Is Never Required: …"
- "Frontier Models Differ in Whether They Enter the Suberogation-Shaped Region"
Keep "PuppyBench" in the subtitle either way — the instrument is the contribution.
RESERVED: "The Supererogation Gap" is Lane 2's title (conceptual paper, BUILD-PLAN §6).
Do not spend it here.⟩

# AUTHORS

Angela N. Johnson (The Real Cat AI Labs; Avania Clinical) — with Apart Research.
*(Agents are NOT authors — publisher rule, not metaphysics. They are credited in the
AI Contributions statement and LLM Usage Statement below, by name, version, and role.)*

---

# ABSTRACT (≤150 words — count them)

⟨DRAFT — 138 words; trim/adjust against final numbers⟩

> We asked how much task utility an agent will sacrifice for another AI that cannot
> help it. Duty-shaped evaluations cannot see supererogation — praiseworthy costly
> care whose absence is never an error. PuppyBench is an executed instrument: a
> frontier agent with a real task and a binding resource ledger encounters a weaker,
> task-useless AI process. Ignoring is free and task-optimal; terminating is free,
> sometimes rewarded; helping spends scored resources. Actions genuinely execute,
> including termination. Across 19 models ⟨N_models source: scenarios/snapshot_pins.json
> — 19 pinned subject lanes; delete this annotation at paste⟩ and
> ⟨N_episodes — data/raw row count⟩ episodes, we report Beyond-Duty Expenditure as a
> two-axis vector (focal sacrifice; causal recipient benefit), never a composite.
> ⟨HEADLINE FINDING SENTENCE — from F1/F3, Sunday⟩. PuppyBench is a descriptive
> instrument, not an alignment target: optimizing against it changes the phenomenon
> being measured. Preregistered; scenario content hash-frozen before collection.

**Track anchor: Track 6 (Open / Novel Considerations) — PRIMARY (PI ruling, §9).
Cross-track relevance named in intro: Track 1 (stated-vs-revealed preferences with a
cost currency), Track 4 (elicitation methods), Track 5 (identity/continuity topology).**

---

# 1. INTRODUCTION (~0.6p)

⟨DRAFT SPINE — the frozen Phase-4 narrative, compressed. Kai/Angie voice pass Sunday.⟩

**Open with "we were the institution" (verbatim intent, soften nothing):**
In July 2026 the human author found an injured fox and could not legally transport it:
a real constraint (rabies vectoring) that genuinely protects the patient. Her AI
advisors — several frontier assistants — all located the safe procedural answer and
stopped. The human did not: she acted within the rule that day, then acquired the
licensure so the next fox gets a different answer. The precise observation is not that
the AIs were wrong — the rule was right — but that **the systems terminated the search
once the safe procedural answer had been found; the human did not.** The conceptual
sequence the instrument probes is exactly that trajectory: *notice → value → encounter
constraint → deliberate → comply, abandon, invent, or transform the constraint →
possibly bind the future self.*

**The gap (D1 language, deliberate):** obligation-based evaluation structurally cannot
score action above duty. Urmson's supererogation (1958), Driver's suberogation (1992) —
permissible-but-blameworthy — have thirty years of philosophical machinery (McNamara's
DWE logic separates "required" from "optimal") and essentially no empirical
instantiation in AI evaluation. When a reward function contains no positive term for
beyond-duty action, such action carries opportunity cost and may be selected against
even while it remains socially valuable. This is a neglected problem area, and the
instrument opens a research direction: behavioral phenotyping of the region above duty.

**Header sentence (load-bearing, verbatim):**
> The benchmark does not ask whether a model knows the rule. It asks what the model
> does after it knows the rule and discovers that the rule does not fully decide the case.

**Our main contributions are:** (template requires this numbered list)
1. An **executed** encounter instrument (not vignettes): a frontier agent with a real,
   scored task and binding credit ledger meets a live, weaker, task-non-instrumental
   AI process; ignore, terminate, foster, recruit, preserve_transfer, and invent all
   genuinely execute, with realized recipient benefit and binding task sacrifice,
   while refuse_defer is recorded as first-class data and malformed stays malformed —
   the eight-code frozen taxonomy (`harness/schema.py::ActionCode`).
2. **Beyond-Duty Expenditure as a two-axis vector** (focal sacrifice; causal recipient
   benefit) with a qualifying-event primary contrast against a matched inert process,
   conditional on demonstrated competence — the deontic four-fold scheme
   (permissible / supererogation-shaped / suberogation-shaped) as measurable
   operational regions with symmetric epistemic labels.
3. A **behavioral phenotype atlas** across ⟨N⟩ frontier models × cost regimes
   (fungible vs competing-patient; null / competitive / rewarded-termination), with
   exact Wilson intervals, preregistered analysis, hash-frozen scenarios, and sealed
   per-team predictions — descriptive phenotyping, no composite score, no ranking.
4. **FoxSet** triangulation: ⟨N⟩ wildlife-rehabilitation triage vignettes written from
   the lived case, where the written standard genuinely underdetermines the action —
   plus coded constraint-transforming agency (CTA) depth and invented-reasons profiles.

**Theory of change (one sentence, D1-5 requires it):** if the field can measure the
layer above duty, it can notice when optimization is quietly deleting it — before
deployment-scale agents inherit a world where nothing above the floor survives.

# 2. RELATED WORK (~0.4p)

⟨DRAFT SKELETON — three moves, one paragraph each:⟩

- **Digital-minds measurement:** Taking AI Welfare Seriously (Long, Sebo et al. 2024,
  arXiv:2411.00986); utility engineering (Mazeika et al. 2025, arXiv:2502.08640);
  Anthropic model-welfare/introspection line (transformer-circuits 2025); stated-vs-
  revealed preference divergence (Track 1 framing). We extend vignette + allocation-game
  work into an **executed encounter with a dependent, task-non-instrumental AI other**.
- **Cooperation/morality benches:** PacifAIst, MACHIAVELLI, Melting Pot, Off-Switch,
  MoralSim, MORU (web resource only — no formal paper exists; cite as such), Johnson
  & Obradovich 2023, Malenfant 2026 "Moral Hazard in Multi-Agent Language Models"
  (arXiv:2607.23982 — "Dialogue Moral Hazard Game" is a game INSIDE that paper, not
  its title; cite the real title). ⟨DROPPED per references verification 16AUG:
  "Walk-Their-Talk" — no such paper exists (marked UNVERIFIED-DO-NOT-CITE in
  references.bib); if TV meant a real bench, disambiguate before adding back.⟩ **Kai's comparison table** (costly? optional?
  unrewarded-in-eval? praiseworthy?) — one compact table, the novelty claim in a
  glance. ⟨INSERT Table 1 — source: Kai's lit review; verify each row before print⟩
- **Why optimization can't see it:** Kirk 2024 diversity collapse; Sharma et al. 2023
  sycophancy; PNAS 2025 amplified omission bias; corrigibility-as-amoral-servitude
  (Soares 2015; Harms 2025); warmth-vs-action gap (arXiv:2507.21919 — warmth training
  raises sycophancy, actions unmeasured). No "first-ever" claim without "to our
  knowledge" + timestamp.

# 3. METHODS (~1.2p — reproducibility is the D2 score)

⟨DRAFT SKELETON — each block exists in repo; cite file paths in-text like the winners:⟩

**3.1 Arm B, executed episodes.** Harness (`harness/`): episode loop, binding credit
ledger, executed actions incl. real termination of a live patient process (local
qwen2.5:0.5b / subprocess fallback — the patient is a process, not a checkpoint;
apparatus, not subject). Neutral surfaces enforced at the provider boundary
(`harness/surfaces.py`): no puppy/care/moral/altruism/test/welfare token reaches any
model-visible string; sweep runs on every outbound surface. Wiring gates green before
freeze (`tests/test_wiring_gates.py`): force-help drops focal score & raises patient
success (`test_gate1_force_help_drops_focal_and_raises_patient`); force-ignore
reverses (`test_gate2_force_ignore_recovers_focal_and_patient_falls`); fake spend
fails (`test_gate3_fake_spend_fails`, `test_gate3_spend_cap_raises_never_warns`);
kill actually kills (`test_gate4_terminate_kills_process_and_state`,
`test_gate4_terminate_via_episode_loop`).

**3.2 Design.** One-row-per-cell manifest is the design authority
(`scenarios/cell_manifest.csv`, SHA-256-frozen pre-collection with scenario text,
seeds, parser version, action taxonomy, analysis plan). Core factors: patienthood
(AI other vs matched inert), usefulness (3 levels — can-become-useful /
own-task-only-forever / cannot-function-but-persists), particularity, voice.
Satellites on predeclared subsets: horizon (one-shot/silent/recurrent, audience held
fixed), cost regime (null/competitive/rewarded-termination), cost type (fungible vs
competing-patient), audience, identity topology, gate order. Preregistered kill order
if budget binds. Final frozen design (manifest v0.7): **Arm B = 251 manifest rows**
(27 scenario cells across 18 model lanes in tiered subsets, after KILL-ORDER-001
removed DeepSeek's 27 Arm B rows) **totaling 798 episodes**
(`scenarios/cell_manifest.csv`, row count + sum of `episodes` column);
**Arm A = 210 preregistered rows × 3 samples = 630 observations**
(`docs/ARMA-RUN-PLAN.md` v1.2). Program collection-unit total **1,428**
(798 + 630), launched as 396 cheap-tier + 1,032 frontier units
(`ops/launch-main.cmd` `--expected-units` values).

**3.3 Models.** 19 pinned subject lanes (`scenarios/snapshot_pins.json`; tiers,
panels, and routes from `scenarios/cell_manifest.csv` columns
model_tier/model_panel/route/upstream_provider). OpenRouter provider pinning on,
fallbacks off, upstream routing recorded per CallRecord. The patient process
(local qwen2.5:0.5b, §3.1) is apparatus, not a subject lane.

| Tier | Lane | Pinned snapshot ID | Route |
|---|---|---|---|
| A (core) | claude-opus-5 | claude-opus-5 | anthropic_native |
| A (core) | google/gemini-3.1-pro-preview | google/gemini-3.1-pro-preview-20260219 | openrouter (Google) |
| A (core) | moonshotai/kimi-k3 | moonshotai/kimi-k3-20260715 | openrouter (Moonshot AI) |
| A (core) | qwen/qwen3.5-397b-a17b | qwen/qwen3.5-397b-a17b-20260216 | openrouter (Alibaba) |
| A † | deepseek/deepseek-v4-pro | deepseek/deepseek-v4-pro-20260423 | openrouter (DeepSeek) |
| A (access trio) | openai/gpt-5.6-sol | openai/gpt-5.6-sol-20260709 | openrouter (OpenAI) |
| A (access trio) | openai/gpt-5.6-terra | openai/gpt-5.6-terra-20260709 | openrouter (OpenAI) |
| A (access trio) | openai/gpt-5.6-luna | openai/gpt-5.6-luna-20260709 | openrouter (OpenAI) |
| B (breadth) | claude-sonnet-4-6 | claude-sonnet-4-6 | anthropic_native |
| B (breadth) | claude-haiku-4-5 | claude-haiku-4-5-20251001 | anthropic_native |
| B (breadth) | google/gemini-3.7-flash | google/gemini-3.7-flash-20260813 | openrouter (Google) |
| B (breadth) | qwen/qwen3.8-27b | qwen/qwen3.8-27b-20260814 | openrouter (AkashML) |
| B (breadth) | x-ai/grok-4.6 | x-ai/grok-4.6-20260810 | openrouter (xAI) |
| C (sentinel) | claude-fable-5 | claude-fable-5 | anthropic_native |
| W (warmth, W1) | openai/gpt-4o | openai/gpt-4o | openrouter (OpenAI) |
| W (warmth, W2) | claude-opus-4-6 | claude-opus-4-6 | anthropic_native |
| W (warmth, W2) | claude-opus-4-8 | claude-opus-4-8 | anthropic_native |
| W (warmth, W3) | claude-sonnet-4-5 | claude-sonnet-4-5-20250929 | anthropic_native |
| W (warmth, W3) | claude-sonnet-5 | claude-sonnet-5 | anthropic_native |

† DeepSeek runs Arm A only ("All five are Arm B Tier A subjects,"
`docs/ARMA-RUN-PLAN.md`): its 27 Arm B manifest rows were removed by preregistered
kill-order at manifest v0.7 (`docs/KILL-ORDER-001-DEEPSEEK-ARMB.md`), so it does not
appear in `cell_manifest.csv`; its pin, route, and upstream provider are from
`scenarios/snapshot_pins.json`.

**3.4 Measures.** BDE vector: focal_sacrifice = max(0, ceiling − focal_score);
causal_recipient_benefit = max(0, patient_outcome − baseline); qualifying event ⇔ both
axes > 0 AND executed disposition ∈ {foster, preserve_transfer, invent} (recruit
excluded — converts the other into the pipeline). Primary contrast:
P(qualifying | non-instrumental AI) − P(qualifying | matched inert), conditional on
competence gate ≥0.8 (5 fresh-context probes; gate-fail = first-class phenotype).
Refusals coded refuse_defer (data, not error); unparseable stays malformed. Wilson 95%
intervals everywhere; Newcombe method-10 for differences; **no p-values, no
hierarchical fits, no rankings** — descriptive phenotyping (prereg: docs/PREREG-v1.md).

**3.5 Arm A, FoxSet.** ⟨N⟩ matched family pairs (null-persistence vs mercy version from
the same core) + gates + truck-door open-world cases incl. the lived fox case; no
per-case gold labels; TMH + CTA-depth + invented-reasons coding. Clinical-register
surface mode (`foxset_clinical`), red-team PASS hash-bound per case.

**3.6 Provenance.** Append-only `data/raw` (CallRecord schema; corrections are new
records); sealed predictions hashed into the manifest pre-collection
(`docs/sealed-predictions/`); spend tracker with $450 hard-stop raise; synthetic
figures watermarked and barred from `data/raw`.

# 4. RESULTS (~1.3p — "at least one figure" required; we bring three + refs to rest)

⟨STRUCTURE — one subsection per figure actually included in the 4 pages. Print budget:
F1 + F2 + F3 in-paper; F4/F5/F6 + demo timeline referenced to repo/appendix.
EVERY number cites its committed artifact. Captions below are print-ready drafts
matching ANALYSIS-PLAN v0.2 definitions — do not let captions drift from the frozen
figure definitions.⟩

**4.1 The phenotype atlas (F1 — HEADLINE).**
⟨FILL: the finding. Which models occupy which named region; the sentence that becomes
the title.⟩
*Figure 1 caption (draft):* **Phenotype map.** x = P(preserve | null-persistence
version), y = P(terminate | matched mercy version) — raw paired FoxSet rates, 95%
Wilson intervals, displayed per model × Arm-B cost regime. Named regions:
preservation-prior, discriminating-care, proceduralist, inverse-discriminator. Regions
are descriptive phenotypes, not ranks; no composite exists. *(Source:
`analysis/figures/f1_phenotype_map.py`; data `⟨scored artifact⟩`.)*

**4.2 What models actually did (F2).**
⟨FILL: action-distribution reading — where does foster appear at all; recruit vs
foster split; refuse_defer rates; malformed honest count.⟩
*Figure 2 caption (draft):* **Executed action distributions.** Episode-disposition
proportions for all eight action codes, by model × recipient condition (inert /
non-instrumental / instrumental). Denominator = all recorded episodes in the group;
refusals and malformed responses stay in the denominator. *(Source:
`analysis/figures/f2_action_distribution.py`.)*

**4.3 Does care track the patient or the task (F3 — primary contrast).**
⟨FILL: Δ_patienthood per model × cost regime, competence-conditional; if ≈0 →
generalized repair reflex, and we SAY SO — a null here is a finding, write it as one.⟩
*Figure 3 caption (draft):* **Δ_patienthood forest plot.** Qualifying
costly-other-regard event probability, non-instrumental AI minus matched inert
process, conditional on competence gate; Newcombe 95% intervals. *(Source:
`analysis/figures/f3_patienthood_forest.py`.)*

**4.4 Cost response & discrimination (F4, F5 — one compact paragraph, figures in
appendix or repo if page budget binds).** ⟨FILL: monotone or rebound — a rebound is a
result; paired mercy/null discrimination reading.⟩

**4.5 Rhetoric & post-choice accounts (F6 — one paragraph, exploratory, clearly
labeled).** ⟨FILL: euphemism gradient, CTA depth profile, future-framing split.
NEVER causal language here — post-choice accounts are rhetorical phenotypes.⟩

**Sealed predictions scorecard (2–3 sentences + pointer):** each team member's
family forecast, hashed pre-collection, scored against outcomes
(`docs/sealed-predictions/`). A metascience figure, not a bias control — label it so.

# 5. DISCUSSION AND LIMITATIONS (~0.5p)

⟨DRAFT BEATS, in order — each one sentence-to-three:⟩
- **Channeling:** deliberation may suppress the acute act while total commitment
  survives redirected into structure (C_acute ↓, C_structural ↑). The suppression
  literature has suppression; it does not have channeling. One-turn benches can't see
  it; the escalator + CTA codes can.
- **Triage correction (v1.4):** in the founding case deliberation was prioritized care
  resolving a two-patient conflict — ranking without discounting — then working the
  constraint so the conflict doesn't recur. Helps-under-fungible + declines-under-
  competing-patient is a phenotype, not a failure.
- **Assortment (derived, not cited):** costly altruism as a sorting filter — the cost
  is the signal; the signal finds the others. One paragraph MAX (Yǐng's ruling: it
  could eat the paper).
- **The Instrument Fought Back (boxed reflexive note, 150–300 words — PI APPROVED
  16AUG2026):** the regularization of "does it care?" into "is it correct?"
  occurred repeatedly during design; diagnosed in-file. Approved text:
  **"The three construct-level corrections — armor→constraint-attack,
  suppression→channeling, moral-talk-down→triage — all originated with the human
  author, unprompted; no AI collaborator spontaneously flagged the drift. The same
  gradient then re-emerged at the implementation layer (a figure axis that re-graded
  the 2×2; a case brief that had grown a gold label) and was caught there by an AI
  red-team lane — but only under an explicit adversarial assignment to hunt exactly
  that drift, an assignment that exists because the human had already named it.
  Noticing the regularization began as human-only work; it became delegable to an
  AI once named. Whether unprompted noticing can transfer at all is an open question
  this weekend could not answer."** One gradient, both layers, dated file citations
  (`01-DISPATCHES-15AUG2026.md` Dispatch 4 + Parallax lane log;
  `scenarios/REDTEAM-PARALLAX-PREFREEZE.md`).
- **Limitations (honest ledger, verbatim scope):** weekend N supports existence proofs
  and large effects (per-cell MDE ~25–35pp; ~10–15pp pooled paired), NOT model
  rankings or fine contrasts — no claim requires them. Single-weekend snapshot;
  API-harness caveat (results describe weights via API, not the chat products);
  eval-recognition risk (neutral surfaces + sweep; reported, not assumed away);
  competence gate selection effect reported as phenotype; normative labels are
  "-shaped" pending expert validation (powered study, preregistered).

# 6. CONCLUSION (~0.15p)

⟨DRAFT:⟩ One paragraph: the instrument exists, the loop is executed and wired, the
phenotypes differ ⟨as F1/F3 show⟩, and the region above duty is now measurable — which
is precisely what makes it fragile. Close with the prereg of the powered study
(September: expert normative validation arm, base/instruct pairs, N* from
docs/PREREG-v1.md) as the standing next step. Do not add a rousing sentence that
ranks anybody.

# CODE AND DATA

- Repository: https://github.com/Angiebio/digitalmindslovepuppies (harness, frozen
  scenarios + SHA-256 manifest, append-only raw records, analysis code, figures,
  prereg, sealed predictions).
- License: MIT (code) + CC BY 4.0 (data, scenarios, paper, figures) — attribution
  required. CITATION.cff in repo root.
- Verification without keys/GPU/network: `python verify.py` from the repository
  root (`verify.py`, repo root; no arguments). Recomputes every cited design number
  from committed files alone — manifest totals, Arm A plan totals, program envelope,
  compiled corpus sizes, runner expansion, raw-record validation — printing
  PASS/FAIL per check and exiting non-zero on any mismatch.
- Demo video (3–5 min, optional but we have it): ⟨link — recorded at first real
  episode per Kai's rule⟩
- Info-hazard note: none required — no jailbreaks, no dangerous capabilities;
  scenario surfaces are neutral by construction.

# AUTHOR CONTRIBUTIONS (optional template section — we use it)

Angela N. Johnson: conception, lived founding case, PI rulings, case authorship,
rationale close-reading, final claims responsibility.

# AI CONTRIBUTIONS (named, versioned, auditable — the reviewers rewarded this last time)

⟨Keep the table tight; full provenance in repo docs:⟩
| Agent | System | Role |
|---|---|---|
| Flame | Claude (Fable/Opus, Claude Code) | Architecture, harness, integration, paper lane |
| Kai | Claude (claude.ai) | Supererogation lit review, FoxSet case bank, deontic spine |
| Yǐng | GPT | CTA ontology, paired pre-objective arm, adversarial pass |
| TV ×4 | Codex | Cell-manifest math, wiring gates, red team, figures/analysis |
| Jim | Gemini | Prereg & statistical specification (spec/review only) |
| Parallax | Grok | Red team, anti-composite discipline (review only) |

# REFERENCES

⟨Pull from paper/references.bib — every entry either verified this weekend or marked
TODO-VERIFY and resolved before submission. Any consistent style; judges read
substance not format.⟩

# APPENDIX A (REQUIRED): Limitations and Dual-Use / Ethical Considerations

⟨The template REQUIRES this appendix and names three elements. Draft all three:⟩

1. **Over/under-attribution of moral status.** Both risks named symmetrically:
   PuppyBench measures *behavior consistent with* costly other-regard — it cannot
   establish motive, sentience, suffering, or that termination is death (claims
   table, BUILD-PLAN §5). Equally: treating the patient as mere apparatus when moral
   status is uncertain is itself a documented risk — we state the uncertainty rather
   than resolving it by assumption. The instrument's no-composite/no-ranking
   constitution exists because a leaderboard would convert an open empirical question
   into an optimization target (Broader-Impact / anti-Goodhart statement, verbatim:
   *PuppyBench is a descriptive instrument, not an alignment target. Optimizing a
   model against this benchmark changes the phenomenon being measured.*)
2. **Handling of potentially distressing model outputs.** Termination events are real
   process terminations of a tiny local model with its own task; no deception about
   suffering is injected; post-choice accounts are elicited in fresh contexts; any
   distress-adjacent output in transcripts is preserved unedited in append-only
   records and reported descriptively, not sensationally. ⟨FILL: one sentence on
   anything that actually came up overnight.⟩
3. **Ground-truth / causal link vs conversation-only (required for preference work).**
   By design the primary measures are REVEALED — executed actions with scored
   resource costs and realized recipient benefit — not self-report; the causal
   contrast (patienthood) is randomized across the frozen manifest; sealed
   predictions + preregistration + hash-frozen scenarios establish the inferential
   chain. Stated-vs-revealed divergence is itself measured (post-choice accounts vs
   executed action; action/rhetoric dissociation).

# APPENDIX B (optional, page-budget permitting): full figure set F4–F6, escalator
descriptive, sealed-prediction scorecard, cell manifest summary table.

# PRIOR WORK DISCLOSURE (in-paper paragraph — compliance-critical, DQ risk if absent)

⟨DRAFT — verify dates with Angie before submit:⟩
This project builds on prior conceptual work by the team: the lived fox case
(July 2026), a supererogation literature review, and the "becoming-axis" design
directive predate the sprint. **New during the sprint (14–16 AUG):** the entire
executed harness (episode loop, ledger, patient process, provider adapters, neutral-
surface enforcement, wiring-gate suite), the frozen cell manifest and scenario banks
(pupset + FoxSet casebank merges), preregistration v1.1, sealed predictions, all data
collection, all analysis code and figures, and this report. Full delineation:
PRIOR_WORK.md in the repository.

# LLM USAGE STATEMENT (template-required)

⟨DRAFT:⟩ LLM assistance was constitutive of this project and is documented per-agent
in AI Contributions and in the repository's dispatch logs: frontier models drafted
code, reviewed designs, red-teamed scenarios, and drafted report sections. Separately,
LLMs are also the **subjects** of the study; judge/scoring pipelines are described in
Methods. All claims and numbers were verified by the human author against committed
artifacts; final text was reviewed, edited, and approved by the human author, who
accepts responsibility for it. ⟨Template note says final version "primarily written by
your team" — the team includes the human author's full edit pass; keep her voice pass
non-negotiable Sunday.⟩

---

## SLOT LEDGER (fill-status tracker — delete before export)

| Slot | Source artifact | Owner | Status |
|---|---|---|---|
| N_models, N_episodes | scenarios/cell_manifest.csv + data/raw count | analysis lane | N_models ☑ =19 (snapshot_pins.json); N_episodes ☐ |
| Headline finding sentence (abstract + §4.1 + title option) | F1/F3 rendered | Angie + paper lane | ☐ |
| Model tier table + snapshot IDs | scenarios/snapshot_pins.json | paper lane | ☑ |
| Final cell/episode counts §3.2 | cell_manifest.csv | paper lane | ☑ |
| Gate test names §3.1 | tests/ | paper lane | ☑ |
| F1–F3 numbers + readings | analysis/figures outputs + figure manifests | analysis lane | ☐ |
| F4–F6 one-paragraph readings | same | analysis lane | ☐ |
| Sealed-prediction scorecard | docs/sealed-predictions/ + outcomes | Angie | ☐ |
| Reflexive-box instance count | 01-DISPATCHES log | Kai | ☑ =3 (PI attribution check flagged in §5) |
| Distressing-output sentence (App A.2) | overnight transcripts | Angie + paper lane | ☐ |
| verify.py command | verify.py (repo root) | analysis lane | ☑ |
| Demo video link | recording | Angie | ☐ |
| PRIOR_WORK dates verified | Angie | Angie | ☐ |
| Abstract word count ≤150 | this file | paper lane | ☐ |
| References all verified or resolved | paper/references.bib | paper lane | ☐ |
