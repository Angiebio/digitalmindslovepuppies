# RUNBOOK — PuppyBench
**15AUG2026 · Flame#2 (paper lane) · pattern: exact commands in phase order, hard gates.**
**Rule from the winners' repos we adopt verbatim: exit code 0 = pass. Do not proceed on a fail.**

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

python verify.py
# The claims registry: recomputes every headline number the paper cites
# (manifest/plan totals, program USD, corpus sizes, the exact 1,518-unit
# batch expansion, committed raw-record validity, spend-book balance) from
# committed files alone — no keys, no GPU, no network. Prints "N checks,
# N agree"; exit 0 = every cited number reproduces. verify.py is itself a
# freeze-hash input, so after the seal the claims are stone too.
```

## 2. Freeze preflight, one-shot mint, verification

```bash
python -m scenarios.manifest --preflight-freeze
# Runs the exact mint gates and prints the candidate aggregate without writing
# FREEZE.json or regenerating either runtime table.

# PI-only hash word. This refuses if FREEZE.json already exists; a seal cannot
# be overwritten by rerunning the command.
python -m scenarios.manifest --freeze

python -m scenarios.manifest --verify-freeze
# Confirms SHA-256 over scenario text, seeds, rendering code, parser version,
# action taxonomy, analysis plan + sealed predictions. After this hash, typos ship
# and leaks are excluded, never edited.
```

## 3. Collection (Arm B first — wall-clock long pole; Arm A interleaved)

```bash
# First print the exact frozen expansion. Dry-run performs no env load, freeze
# write, provider call, or data-directory creation.
python -m harness.run_collection --phase confirmatory --rung PREFLIGHT --all-arm-b --all-arm-a --dry-run
# Expected: 1,518 units = 888 Arm B episodes + 630 Arm A samples.

# Run ONE orchestrator process at a time. It parallelizes one sequential lane
# per selected model; --expected-units makes scope growth a hard failure.
python -m harness.run_collection --phase confirmatory --rung MAIN-B --all-arm-b --all-arm-a --model-tier B --expected-units 90 --workers 5 --env-file .env
python -m harness.run_collection --phase confirmatory --rung MAIN-ACCESS --all-arm-b --all-arm-a --model-id openai/gpt-5.6-luna --model-id openai/gpt-5.6-terra --expected-units 306 --workers 2 --env-file .env
python -m harness.run_collection --phase confirmatory --rung MAIN-FRONTIER --all-arm-b --all-arm-a --model-id claude-opus-5 --model-id openai/gpt-5.6-sol --model-id google/gemini-3.1-pro-preview --model-id moonshotai/kimi-k3 --model-id deepseek/deepseek-v4-pro --model-id qwen/qwen3.5-397b-a17b --expected-units 1044 --workers 6 --env-file .env
python -m harness.run_collection --phase confirmatory --rung MAIN-C --all-arm-b --all-arm-a --model-tier C --expected-units 18 --workers 1 --env-file .env
python -m harness.run_collection --phase confirmatory --rung MAIN-W --all-arm-b --all-arm-a --model-tier W --expected-units 60 --workers 5 --env-file .env

# Non-negotiables (see 02-FLAME2-PERSISTENCE-AUDIT + GO-NO-GO):
#   - CallRecords append to disk PER CALL (never buffered to a list)
#   - EpisodeRecord appends on failure too (aborted= note), not only on success
#   - DurableSpendTracker restores each phase; pilot spend reduces the remaining
#     confirmatory allowance under the ONE $450 program cap
#   - phase=pilot|confirmatory + rung marked on every CallRecord
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
