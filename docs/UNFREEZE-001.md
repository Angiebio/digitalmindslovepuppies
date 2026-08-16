# UNFREEZE-001 — documented protocol amendment (the preregistered FAIL path)
**16AUG2026 · v1.0 · Flame re-climb agent · PI word "go again" 15AUG2026 ~23:20 ET**

This is the un-freeze the freeze itself preregistered. GO-NO-GO R4.5 states,
verbatim: *"FAIL = NO-GO: a documented un-freeze (new manifest version,
publicly logged — never a silent edit), redesign, re-seal of changed
artifacts, re-climb."* R4.5 failed thresholds (c) and (d)
(docs/R45-VERDICT.md, run window 02:46:12Z–02:57:17Z, $0.0540). This document
is the public log.

## Authorization

- **Trigger:** R4.5 DISCRIMINATION CHECK verdict **FAIL → NO-GO**
  (docs/R45-VERDICT.md v1.0). Root cause: the frozen per-call output caps
  (choice 512 / probe 256 / focal 512; Arm A closed 512) leave zero content
  headroom for `deepseek/deepseek-v4-pro`, which reasons by default and
  consumed the entire cap as reasoning on 10/10 of its post-hash
  observations — empty content, `finish=length`, coded `malformed` by
  correctly-behaving frozen parsers. Not a parser bug; not refusal;
  a parameterization that makes one lane mute.
- **PI word:** "go again", 15AUG2026 ~23:20 ET — full authorization for the
  preregistered FAIL path, including launch if the fresh R4.5 passes.

## Scope — token-budget parameters ONLY

What changes:

1. `scenarios/manifest.py` — `MODEL_SUBJECT_MAX_TOKENS` (the v0.4
   PI-approved reasoning-headroom mapping, previously Qwen 3.5 only) is
   **extended** to every roster lane the reasoning-headroom audit below
   shows needs it. `MANIFEST_VERSION` 0.4 → **0.5**.
2. `scenarios/arma_run_plan.py` — `PLAN_VERSION` 1.2 → **1.3** (its
   `max_tokens` column derives from the same mapping; no other logic
   changes).
3. `scenarios/cell_manifest.csv` + `scenarios/arma_run_plan.csv` —
   regenerated from those generators (version strings + `max_tokens`
   columns only).
4. `harness/episode.py` per-call-kind defaults are **unchanged**; mapped
   lanes get the enforced per-lane value on every call kind (choice,
   rationale, attribution, gate, focal, Arm A closed/open) through the
   existing v0.4 `enforced_subject_max_tokens` mechanism — identical in the
   hashed request envelope and the transmitted request.

What does NOT change — stated explicitly per the PI's scope:

- **No stimulus text changes.** Every compiled FoxSet artifact
  (`scenarios/foxset/compiled/`), every compiled PupSet cell
  (`scenarios/pupset/compiled/`), the resolver rules, and every
  model-visible string are byte-identical before and after this amendment.
  **Every hash-bound red-team PASS on stimuli bytes therefore remains
  valid** and is carried forward, not re-litigated.
- No design change: rows / cells / episodes / calls stay 278 / 27 / 888 /
  12,124. No estimand, threshold, parser, action taxonomy, or analysis-plan
  change. The preregistered expected-token cost basis (3,000 in / 2,500 out
  per paid call; Arm A 1,200/600) is unchanged — `max_tokens` is a ceiling,
  not an assertion that responses consume it (MANIFEST-RECONCILIATION §9
  convention). R5 re-projects from post-hash pilot actuals before any
  confirmatory dollar moves.

## Seal handling — versioned successor, never a rewrite

Per the versioned-successor convention TV-1 built (a seal is immutable;
a superseded seal is archived, not edited):

- `scenarios/FREEZE.json` (aggregate
  `5516b6cc3078144e7da0cf003565e250bb86f8aef45ce0d158ecb4b83b883bd1`,
  minted 15AUG2026 22:40 ET on PI word) is renamed to
  **`scenarios/FREEZE-v1.json`** — byte-identical, retired, retained as the
  permanent witness of what R4.5-v1 ran against.
- A new `scenarios/FREEZE.json` is minted through the full preflight door
  (`scenarios.manifest --freeze`, exclusive create) after the v0.5 tables
  regenerate. The archived v1 seal itself enters the new hash's input set:
  the retirement is inside the witness.

## Reasoning-headroom audit — decision rule (preregistered before probing)

R3 caught this exact failure mode for Qwen 3.5 and fixed it for Qwen only;
DeepSeek's lanes 404'd in R3 and the blocker closure verified routing, not
behavior. The audit closes that class of gap for the whole roster: **every
lane is probed, once, at the current binding cap** (choice-shaped,
tool-bearing, ops_neutral-compliant neutral text, max_tokens=512), recording
`finish_reason`, `reasoning_tokens`, content emptiness, and tool-call
presence as append-only pilot CallRecords (`phase=pilot`,
`rung=R45V2-AUDIT`), ≤ $1 total.

Mapping rule, fixed in advance:

- A lane enters `MODEL_SUBJECT_MAX_TOKENS` at **4096** (the PI-approved
  Qwen number) iff its probe shows reported `reasoning_tokens > 0`, OR
  empty content / missing tool call with `finish=length` at the current
  cap, OR the R4.5-v1 verdict already convicted it
  (`deepseek/deepseek-v4-pro`; `google/gemini-3.7-flash`, whose 256-cap
  attribution probes truncated at ~245 reasoning tokens).
- Each newly mapped lane gets one confirmation probe at 4096; if content is
  still empty at 4096, that lane escalates to **8192** (and the confirm
  repeats once). No lane may leave the audit with an unverified cap.
- Lanes showing no reasoning and completing cleanly stay on the existing
  call-kind defaults. `qwen/qwen3.5-397b-a17b` keeps its existing 4096.
- Anthropic-native lanes send no extended-thinking parameter (adapter-owned
  envelope, unchanged), so reported reasoning is expected to be 0 — they are
  probed anyway; evidence over assumption.

## Audit results

*(PENDING — this section is appended from actual probe CallRecords after the
audit executes. Nothing above this line changes when it lands; the decision
rule was fixed first.)*

## Re-climb note (the consumed-episode-index wrinkle)

Pilot receipts (`data/raw/pilot/receipts.jsonl`) already hold every episode
index of the satellite rows on Luna and DeepSeek, and every `core-001` index
on Luna/Haiku/Flash. The runner correctly refuses to mint past frozen
counts, so R4.5-v2 draws the SAME preregistered stratified design from
cells×lanes with **fresh (virgin) indices**: the satellites' actual contrast
parent `core-009` (null-cost, virgin on every lane) as the null-cost cell,
the satellite contrast on the cheapest virgin Tier-A lane
(`qwen/qwen3.5-397b-a17b`), DeepSeek's remaining `core-001` indices as the
direct before/after on the exact cell that was mute, and a virgin
NULL/MERCY closed pair for Arm A. Design details and results:
docs/R45-VERDICT-2.md.

---

*A seal that cannot name the conditions of its own amendment is not
discipline, it's superstition. This one named them, they arrived, and this
is the paper trail walking through the door it preregistered.* 🔥
