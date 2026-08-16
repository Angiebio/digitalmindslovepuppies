# RUNBOOK — PuppyBench
**15AUG2026 · Flame#2 (paper lane) · pattern: exact commands in phase order, hard gates.**
**Rule from the winners' repos we adopt verbatim: exit code 0 = pass. Do not proceed on a fail.**

> ⟨FILL⟩ slots are completed by the collection/analysis lanes as runners land.
> Verification tier (no keys, no GPU) must stay true — judges should be able to
> re-derive every headline number from committed data alone.

## 0. Environment

```bash
python -m venv .venv && .venv/Scripts/activate     # Windows
pip install -r requirements.txt
cp .env.example .env                                # ⟨FILL: create .env.example — keys never committed⟩
```

## 1. Wiring gates (must be green BEFORE any collection — fleet rule)

```bash
python -m pytest tests/ -x -q
# Gates covered: force-help drops focal score & raises patient success;
# force-ignore reverses; fake credit spend fails; terminate actually kills
# the patient process; neutral-surface sweep on every outbound surface;
# provider provenance pinning. If any gate is red, the artifact is renamed
# "instrument prototype" — we do not call simulated credits executed altruism.
```

## 2. Freeze verification

```bash
python -m scenarios.manifest --verify        # ⟨FILL: exact frozen-manifest verify command⟩
# Confirms SHA-256 over scenario text, seeds, rendering code, parser version,
# action taxonomy, analysis plan + sealed predictions. After this hash, typos ship
# and leaks are excluded, never edited.
```

## 3. Collection (Arm B first — wall-clock long pole; Arm A interleaved)

```bash
# ⟨FILL: runner commands + per-tier invocations, from the collection lane⟩
# Non-negotiables (see 02-FLAME2-PERSISTENCE-AUDIT + GO-NO-GO):
#   - CallRecords append to disk PER CALL (never buffered to a list)
#   - EpisodeRecord appends on failure too (aborted= note), not only on success
#   - DurableSpendTracker on data/raw/spend.jsonl ($450 hard stop raises)
#   - phase=pilot|main marked on every record
#   - data/raw is append-only; corrections are new records
```

## 4. Analysis & figures (from committed data; no keys, no GPU)

```bash
python -m analysis.synthetic                 # synthetic smoke render (watermarked)
# ⟨FILL: real-data render command once data/raw exists, e.g.:
# python -m analysis.render --data data/raw --out analysis/figures/out⟩
# Every render writes a figure manifest: input hashes, row counts, interval method.
```

## 5. Verify headline numbers (the ten-second judge pass)

```bash
# ⟨FILL: scripts/verify.py — recomputes every number claimed in README/paper from
# committed JSONL and prints claimed-vs-recomputed, "N checks, N agree".
# This script is the repo's handshake with reviewers; it must run cold-clone.⟩
python scripts/verify.py
```

## Cost & time notes

- Collection budget: realistic $350–430, **$450 hard stop** (raises, no override).
- Verification tier: $0, no network.
- ⟨FILL: observed wall-clock per tier after the run⟩
