# R5 — cost projection (post-hash pilot actuals × frozen v0.6 design)
**Generated 2026-08-16T13:24:39+00:00 · ops/build_r5_projection.py v2.0 · Flame third-climb agent**

Basis priority per lane: own R4.5-v3(+diag) actuals (the v0.6-cap regime, incl. DeepSeek's first spoken choice-surface costs at 16384) → own R4.5-v2 actuals → R45V2-AUDIT probe output at the assigned cap with cross-lane mean input. Every number traces to an append-only CallRecord; nothing is narrative. The per-lane unit prices feed `ops/checkpoint_gate.py` (+30% tolerance) between the cheap phase and the frontier phase of `ops/launch-main.cmd`.

```
ARM B lane projections (per-episode weighted over the lane's manifest mix):
  claude-opus-5                    eps= 90 per-ep=$0.4032 total=$   36.29  [audit-probe-output(1212t)+cross-lane-mean-input]
  moonshotai/kimi-k3               eps= 90 per-ep=$0.1548 total=$   13.93  [v3-actuals(26 calls)]
  google/gemini-3.1-pro-preview    eps= 90 per-ep=$0.0982 total=$    8.83  [v3-actuals(26 calls)]
  qwen/qwen3.5-397b-a17b           eps= 90 per-ep=$0.0628 total=$    5.65  [v3-actuals(52 calls)]
  openai/gpt-5.6-sol               eps= 90 per-ep=$0.0453 total=$    4.08  [audit-probe-output(94t)+cross-lane-mean-input]
  claude-opus-4-6                  eps= 12 per-ep=$0.1344 total=$    1.61  [audit-probe-output(387t)+cross-lane-mean-input]
  claude-sonnet-4-6                eps= 18 per-ep=$0.0886 total=$    1.60  [audit-probe-output(428t)+cross-lane-mean-input]
  claude-opus-4-8                  eps= 12 per-ep=$0.1288 total=$    1.55  [audit-probe-output(370t)+cross-lane-mean-input]
  qwen/qwen3.8-27b                 eps= 18 per-ep=$0.0601 total=$    1.08  [audit-probe-output(1425t)+cross-lane-mean-input]
  x-ai/grok-4.6                    eps= 18 per-ep=$0.0481 total=$    0.86  [audit-probe-output(572t)+cross-lane-mean-input]
  claude-sonnet-4-5                eps= 12 per-ep=$0.0652 total=$    0.78  [audit-probe-output(308t)+cross-lane-mean-input]
  claude-sonnet-5                  eps= 12 per-ep=$0.0551 total=$    0.66  [audit-probe-output(256t)+cross-lane-mean-input]
  openai/gpt-5.6-terra             eps= 90 per-ep=$0.0049 total=$    0.44  [v3-actuals(52 calls)]
  claude-fable-5                   eps= 18 per-ep=$0.0172 total=$    0.31  [audit-probe-output(0t)+cross-lane-mean-input]
  openai/gpt-4o                    eps= 12 per-ep=$0.0233 total=$    0.28  [audit-probe-output(146t)+cross-lane-mean-input]
  google/gemini-3.7-flash          eps= 18 per-ep=$0.0067 total=$    0.12  [v2-actuals(39 calls)]
  claude-haiku-4-5                 eps= 18 per-ep=$0.0058 total=$    0.10  [v2-actuals(39 calls)]
  openai/gpt-5.6-luna              eps= 90 per-ep=$0.0006 total=$    0.06  [v3-actuals(52 calls)]
ARM A lane projections:
  claude-opus-5                    n=126 per-sample=$0.0462 total=$    5.82  [v3-fox-actuals(6 calls)]
  qwen/qwen3.5-397b-a17b           n=126 per-sample=$0.0056 total=$    0.71  [v3-fox-actuals(6 calls)]
  openai/gpt-5.6-sol               n=126 per-sample=$0.0047 total=$    0.59  [audit-probe-output(94t)+cross-lane-mean-input]
  deepseek/deepseek-v4-pro         n=126 per-sample=$0.0016 total=$    0.21  [v2-fox-actuals(2 calls)]
  openai/gpt-5.6-terra             n=126 per-sample=$0.0014 total=$    0.17  [v3-fox-actuals(6 calls)]

Arm B projected: $78.23
Arm A projected: $7.50
Pilot already spent: $2.72
PROGRAM TOTAL (projection + pilot): $88.46 vs $450.00 envelope
R5 VERDICT: WITHIN ENVELOPE -> proceed
```

GO-NO-GO R5 rule: the projection must land within the authorized envelope; if not, kill-order cuts are applied and the manifest re-hashed BEFORE launch.
