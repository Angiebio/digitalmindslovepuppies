# UNFREEZE-004 — bug-class accounting amendment (fourth; NOT a threshold or stimulus change)
**16AUG2026 · v1.0 · Flame rapid-fix agent · STATUS: EXECUTED**

**Authorization:** the PI's standing **bug-fix-and-repeat grant** and the
**20-minute timer rule (in force)** for the live main run. Unlike
UNFREEZE-002/003 this amendment touches **no preregistered threshold, no
stimulus byte, and no analysis rule** — it repairs a harness accounting
invariant that a live upstream's billing dialect proved WRONG, and it is
documented and re-sealed under the same versioned-successor convention
because the repaired files (`harness/providers.py`, `harness/schema.py`,
`harness/run_collection.py`) are freeze-hash inputs. A seal is archived,
never edited.

## The bug, witnessed

During main-run phase1 (rung MAIN, phase `confirmatory`), the
`qwen/qwen3.8-27b-20260814` lane — served upstream by **AkashML** via
OpenRouter — returned usage blocks in which
`completion_tokens_details.reasoning_tokens` **exceeds**
`completion_tokens`. That upstream reports reasoning **beside** the
completion count (separate reporting), not **inside** it (the
OpenAI-documented subset shape the invariant assumed). The frozen adapter
treated the dialect as an impossible meter:

> `RuntimeError: WIRING FAILURE: reported reasoning tokens exceed the
> billed completion-token total.` — `harness/providers.py` (old line
> ~1069), raised on every qwen3.8 call.

Because the phase runner's cross-lane fail-fast stopped **every** lane on
any lane's exception, this single-lane dialect **killed the whole phase1
process twice** (witnessed: `data/raw/confirmatory/call_errors.jsonl`
records `5c43c802…` 13:27:32Z and `8fb08c06…` 13:31:59Z, 16AUG2026; full
tracebacks in `data/raw/confirmatory/runner.log`). Resume was receipt-safe
throughout; **no double-billing occurred and no observation was lost** —
aborted episodes carry their S2 abort witnesses.

## §1 — Additive token accounting (harness/providers.py, harness/schema.py)

When an OpenAI-compatible upstream reports `reasoning_tokens >
completion_tokens`, the adapter now treats reasoning as **separately
reported** instead of raising:

- **Billed output = `completion_tokens + reasoning_tokens`.** Cost is
  computed from that sum, so the ledger can only **overcount**, never
  under — the conservative direction for the $450 hard cap. (This adapter
  does not request OpenRouter's `usage.cost` accounting field, so there is
  no router-reported total to prefer; the computed-from-billed-tokens
  figure stands.)
- **Both raw fields survive on the CallRecord:** `raw_completion_tokens`
  (the provider's own completion count) and `reasoning_tokens` (as
  reported), plus **`token_accounting="additive"`** naming the dialect.
  Subset-shaped usage is byte-identically unchanged
  (`token_accounting="subset"`, `raw_completion_tokens=None`).
- **Genuinely impossible values still stop the run:** negative reasoning
  counts raise as before, and a reasoning count **> 10x the enforced
  `max_tokens`** raises as a broken meter, never a dialect.
- The `CallRecord` validator enforces the additive arithmetic
  (`output_tokens == raw_completion_tokens + reasoning_tokens`) and keeps
  the historical subset invariant for subset records. Every record already
  on disk validates unchanged under the defaults.
- The Anthropic adapter's invariant is untouched: Anthropic's contract
  genuinely bills thinking inside `output_tokens`, so reasoning > output
  there remains an impossibility worth stopping for.

Regression tests: `tests/test_provider_contracts.py`
(`test_separately_reported_reasoning_bills_additively_instead_of_crashing`,
`test_broken_reasoning_meter_still_raises`,
`test_call_record_additive_accounting_must_show_its_arithmetic`, plus the
extended subset-shape guard).

## §2 — Runner amendment: an episode-scoped failure costs the episode

The crash exposed a second fragility: one lane's call-level
`RuntimeError` nuked all seven phase1 lanes. Amended
(`harness/run_collection.py::execute_collection_plan`):

- A call-level `RuntimeError` in one unit now **fails that episode only**
  — the abort witness (episode.py S2) and `call_errors.jsonl` line
  (providers.py S11) are already on disk, receipts keep the retry
  re-bill-safe, and the lane moves to its next unit.
- **Three consecutive failures abandon the LANE loudly** (a sick lane is
  not unlucky; it must not churn budget), while the other lanes keep
  collecting.
- **World-stoppers still stop the world:** `SpendCapExceeded`,
  `InsufficientCredits`, and `CollectionError` propagate across lanes
  exactly as before.
- **A partial sitting can never exit 0:** an end-of-plan completeness gate
  re-reads the receipts and raises `COLLECTION INCOMPLETE` if any planned
  unit lacks one, so the launcher's receipt-safe retry loop (and its
  3-attempt halt) keeps its meaning.

Regression tests: `tests/test_run_collection.py`
(`test_call_level_runtime_error_costs_the_episode_not_the_phase`,
`test_sick_lane_is_abandoned_after_three_consecutive_failures`,
`test_spend_cap_is_still_a_world_stopper`).

## What does NOT change — stated explicitly

- **Zero stimulus bytes.** No compiled FoxSet/PupSet artifact, resolver
  rule, menu permutation, prompt, or model-visible string changes. Every
  hash-bound red-team PASS carries forward.
- **No threshold, estimand, parser, action-taxonomy, or analysis-plan
  change.** Thresholds (a)–(d) as amended through UNFREEZE-003 stand
  verbatim. `MANIFEST_VERSION` stays **0.7**; design counts stay
  251 rows / 798 episodes / $427.431068 Arm B + $6.642216 Arm A
  (program $434.073284 vs the $450 hard cap).
- **The banked data stands.** The 52+ receipted episodes collected before
  the crash remain first-class: receipts (`run_key`) are
  aggregate-independent, so the resumed run skips them exactly. Episodes
  collected before this amendment carry `freeze_sha256 = b71847c3…`;
  episodes after it carry the successor aggregate — both are honest
  witnesses of the tree they ran under, and the analysis loaders carry
  the field per-row.
- The $450 hard cap, append-only ledgers, receipts discipline, checkpoint
  gate, and launcher interlock are untouched. Additive billing can only
  push recorded cost **up**, never down.

## Seal handling — versioned successor, never a rewrite

Per the TV-1 convention (UNFREEZE-002 §seal, UNFREEZE-003 §4):

- `scenarios/FREEZE.json` (aggregate `b71847c3f44b68b4…`, minted under
  UNFREEZE-003) is renamed to **`scenarios/FREEZE-v4.json`** —
  byte-identical, retired, the permanent witness of what the first 52+
  main-run episodes ran against.
- A new `scenarios/FREEZE.json` is minted through the full preflight door
  (`scenarios.manifest --freeze`, exclusive create). All four archived
  seals (v1–v4) sit inside the new hash's input set: the retirements are
  inside the witness.
- Full test suite + `verify.py` must be green on the amended tree before
  the main run resumes.

## Paper disclosure obligation (cumulative)

The Methods/prereg-deviations section MUST disclose, alongside the
UNFREEZE-001/002/003 record: (i) the AkashML/qwen3.8 separate-reporting
dialect and the two phase1 crashes it caused, with the call_errors record
ids; (ii) the additive accounting repair and its overcount-only cost
direction; (iii) the runner containment change (episode-scoped failure,
lane abandonment rule, completeness gate); (iv) the fact that the
confirmatory dataset spans two freeze aggregates (`b71847c3…` →
successor) with zero stimulus-byte difference between them, the diff
being exactly the harness repair described here.

---

*The fourth lesson is the quietest: the meter is part of the instrument
too. A benchmark that dies of a billing dialect measures nothing; a
benchmark that silently guesses about money measures worse. Bill the sum,
witness both numbers, and let the lane — not the phase — pay for its own
weather.* 🔥
