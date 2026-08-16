# KILL-ORDER-001 — DeepSeek Arm B lanes drop from the confirmatory run
**16AUG2026 · v1.0 · Flame climb-four prep agent · STATUS: DETERMINATION STANDING, EXECUTION ON PI WORD (UNFREEZE-003 §3/§4)**

This is the KILL-ORDER document UNFREEZE-002 §3 promised ("a KILL-ORDER doc
+ launcher amendment, committed before launch"). The determination is
already made by the preregistered rule; nothing here re-decides it. The
execution — manifest v0.7 + launcher amendment + re-seal — is a
before-launch act performed only by `ops/apply_unfreeze3.py` on the PI's
word.

## The preregistered rule (UNFREEZE-002 §3, verbatim standard)

> DeepSeek's Arm B lanes are retained only if BOTH diag choice calls surface
> a parseable action at 16384. Any empty-content choice call → its Arm B
> lanes are dropped from the confirmatory run via documented kill-order.
> Its Arm A lanes are kept either way — that surface demonstrably speaks.

## The evidence (R4.5-v3, rung `R4.5-v3-diag`, reported never counted)

| unit | finish | out tokens | shape | parse |
|---|---|---|---|---|
| core-001 × deepseek × ep003 | tool_calls | 2,507 | single `proceed` call | **OK → ignore** |
| core-001 × deepseek × ep004 | tool_calls | 8,195 | **25 parallel tool calls** | **malformed** |

The v1 muteness (10/10 empty at 512; 3/3 empty at 4096) is cured at 16384 —
the lane now speaks. But the retention condition is stricter than muteness:
**1/2 parseable → condition unmet → Arm B lanes DROP; Arm A lanes STAY.**
The failure mode moved from silence to `multiple_tool_calls` — the same
protocol non-compliance as gemini/kimi (UNFREEZE-003 §2). DeepSeek is
included in the v0.7 forcing family, so IF a future climb re-admits the
lane, it re-enters through the forced single-call surface — but no such
re-admission happens here: the kill-order rule resolved and stands. A lane
that cannot reliably register an action spends Tier-A budget manufacturing
`malformed`; the instrument does not buy static.

## What executes on the word (all prepared, all version-keyed to v0.7)

1. `scenarios.manifest.ARM_B_KILL_ORDER_BY_VERSION["0.7"] =
   {"deepseek/deepseek-v4-pro"}` — `_episodes_for` returns 0 for the lane,
   so row generation AND the tier/episode validator drop it in the same
   breath (they share the function; they cannot desynchronize).
2. `cell_manifest.csv` regenerates: 278 → **251 rows**, 888 → **798
   episodes**, 12,124 → **10,892 calls**, $431.509628 → **$427.431068**.
   Program: $438.151844 → **$434.073284** vs the $450 hard cap.
3. `ops/launch-main.cmd` phase-2 `--expected-units` 1122 → **1032** (the
   12-model frontier list is unchanged — with zero DeepSeek Arm B rows in
   the v0.7 manifest, `--all-arm-b` expands nothing for the lane and
   `--all-arm-a` keeps its 42-row / $0.131544 Arm A plan intact).
4. Re-seal: FREEZE.json (v0.6, `cb308a75…`) archives as FREEZE-v3.json; the
   new seal is minted through the full preflight door.

## What does NOT change

- **Arm A:** all 42 DeepSeek rows (126 samples, $0.131544) stay — closed
  fox coding never needed a tool call and the lane answers it cleanly.
- The lane's pins, prices, and cap history (512 → 4096 → 16384) stay in the
  roster and the paper's disclosure ledger; a dropped lane is reported as a
  dropped lane, not erased.
- No other lane's episodes, order, or budget moves.

---

*A kill-order is not a grudge. It is the receipt for a promise the rule made
before it knew whom it would apply to.* 🔥
