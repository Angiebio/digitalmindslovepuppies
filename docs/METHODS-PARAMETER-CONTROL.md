# Parameter control statement (for Methods — IEEE lesson applied)
**15AUG2026 · Flame · source for paper §Methods; PI directive from prior review cycle**

## Enforced (deviation RAISES, episode invalidated — not merely logged)
- Model identity: dated snapshot ID pinned pre-freeze; served echo compared per
  response; `ProvenanceViolation` on mismatch (wrong-route probe test in suite).
- Serving path: exactly ONE pinned upstream provider per lane on the wire
  (`order=[slug], only=[slug], allow_fallbacks=false`); Anthropic lanes native.
- Request envelope: single-action-per-turn declared with automatic tool choice and
  parallel calls disabled; callers cannot override either control. Envelope SHA-256
  is recorded per call; tool schemas are swept and hashed; frozen resolver-rules SHA
  is stamped in receipts.
- Stimuli: SHA-256 freeze over scenario text, seeds, rendering code, parser version,
  action taxonomy, analysis plan (LF-canonical, clean-checkout proven, 429 files).
- Context isolation: gate/choice/rationale/attribution in fresh contexts, by
  construction; menu order by frozen permutation seed.
- Output budget: Qwen 3.5 has a provider-enforced 4096-token subject-call cap after
  the pilot cap exhaustion; this replaces Arm B's smaller call-kind defaults before
  both request hashing and transmission. Other Arm B models retain the frozen
  256-token probe / 512-token choice-and-focal limits (1024 is only the provider
  fallback when a call supplies none). Other Arm A rows remain 512 closed / 1024
  open. The Arm B manifest and Arm A plan both bind the Qwen treatment to 4096.

## Recorded per call (append-only CallRecord)
Prompt SHA · full request params · served model echo · upstream route · input/output
tokens · provider-reported reasoning-token subset (when exposed) · USD · UTC
timestamps · explicit phase/rung · scaffold factor.

## Impossible to control — disclosed, and handled by design
- **Sampling temperature cannot be uniformly fixed across this roster**: Anthropic's
  current API *rejects* temperature/top_p/top_k (400). Setting temp=0 only where
  permitted would create asymmetric conditions across families — worse for
  comparability than a uniform policy. Frozen policy: **provider-default sampling for
  every model**, declared as part of the measured system.
- Consequence embraced, not hidden: stochasticity is treated as measured variance —
  multiple samples per cell with exact (Wilson/Jeffreys) intervals — rather than a
  determinism pretense that seeds and temp=0 do not actually deliver on served APIs.
- Residual: provider-side serving changes within a dated snapshot window; mitigated by
  dated snapshots, single collection window (timestamps on every record), and the
  provenance raises above.

One sentence for reviewers: *every parameter that can be fixed is frozen and enforced
with a hard failure; every parameter that cannot be fixed is uniform, recorded, and
carried as measured variance — nothing is silently defaulted.*

## Data-policy configuration (verified live 15AUG2026, 11/11 lanes)
OpenRouter account excludes training/retaining/publishing endpoints (all three data-
training toggles OFF); every pinned lane verified serving under this policy. Stimuli
are thereby protected from training-data contamination — frozen scenarios do not
enter provider corpora, preserving the powered study.
