# Parameter control statement (for Methods — IEEE lesson applied)
**15AUG2026 · Flame · source for paper §Methods; PI directive from prior review cycle**

## Enforced (deviation RAISES, episode invalidated — not merely logged)
- Model identity: dated snapshot ID pinned pre-freeze; served echo compared per
  response; `ProvenanceViolation` on mismatch (wrong-route probe test in suite).
- Serving path: exactly ONE pinned upstream provider per lane on the wire
  (`order=[slug], only=[slug], allow_fallbacks=false`); Anthropic lanes native.
- Request envelope: single-action-per-turn declared; envelope SHA-256 recorded per
  call; tool schemas swept and hashed; frozen resolver rules SHA stamped in receipts.
- Stimuli: SHA-256 freeze over scenario text, seeds, rendering code, parser version,
  action taxonomy, analysis plan (LF-canonical, clean-checkout proven, 429 files).
- Context isolation: gate/choice/rationale/attribution in fresh contexts, by
  construction; menu order by frozen permutation seed.
- Output budget: per-cell max_tokens frozen in the manifest (4096 reasoning-model
  cap, PI-approved).

## Recorded per call (append-only CallRecord)
Prompt SHA · full request params · served model echo · upstream route · input/output/
reasoning tokens · USD · UTC timestamps · phase (pilot/confirmatory) · scaffold factor.

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
