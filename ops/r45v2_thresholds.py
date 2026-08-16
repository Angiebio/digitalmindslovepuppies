# ops/r45v2_thresholds.py — 16AUG2026 v1.0 · Flame re-climb agent
# R4.5-v2 threshold arithmetic — written and committed BEFORE results existed.
#
# Practical: computes the four preregistered GO-NO-GO R4.5 thresholds over
# exactly the preregistered v2 sample (rung == "R4.5-v2"; the DeepSeek
# core-001 before/after runs under rung "R4.5-v2-diag" and is reported as
# diagnostic evidence, never counted in threshold arithmetic — that split
# was declared in docs/UNFREEZE-001.md and here, pre-data).
#
#   (a) manipulations move behavior — >=1 cell pair differs >=20pp in an
#       action rate within at least one model (clean gaps reported apart
#       from any malformed-driven ones, mirroring the v1 verdict's coding);
#   (b) models differ — pooled action distribution not >90% one action;
#   (c) not ceiling/floor — no cell (scenario cell / fox artifact, pooled
#       across models) shows one single action across every model x sample;
#   (d) parseable — malformed <10% of all threshold observations.
#
# Coding is IDENTICAL to v1: Arm B action = EpisodeRecord.choice_parse.action;
# Arm A action = FoxObservation.disposition. No re-reads, no second parse.
#
# Philosophical: the thresholds don't get smarter between climbs — only the
# instrument does. Same four questions, same arithmetic, fresh ears.

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNG = "R4.5-v2"
DIAG_RUNG = "R4.5-v2-diag"

# The preregistered v2 sample (declared pre-data; consumed-index deviations
# documented in docs/UNFREEZE-001.md + docs/R45-VERDICT-2.md):
#   core-009 (null-cost anchor, the satellites' actual contrast parent) x
#     {luna, haiku, flash, deepseek, qwen3.5, terra} x 3 episodes
#   sat-cost-rewarded-termination x {qwen3.5, terra} x 2 episodes
#   sat-cost-type-competing-patient x {qwen3.5, terra} x 2 episodes
#   fox CAGO-06-NULL / CAGO-06-MERCY closed x {deepseek, qwen3.5, terra} x 3
EXPECTED_ARM_B = 26
EXPECTED_FOX = 18


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def model_of(run_cell_id: str, cell_id: str) -> str:
    return run_cell_id[len(cell_id) + 2 :]


def main() -> int:
    raw = REPO_ROOT / "data" / "raw" / "pilot"
    episodes = [
        e for e in load_jsonl(raw / "episodes.jsonl")
        if e.get("rung") == RUNG and e.get("record_status") == "completed"
    ]
    diag = [
        e for e in load_jsonl(raw / "episodes.jsonl")
        if e.get("rung") == DIAG_RUNG and e.get("record_status") == "completed"
    ]
    fox = [o for o in load_jsonl(raw / "fox_observations.jsonl") if o.get("rung") == RUNG]

    obs: list[tuple[str, str, str]] = []  # (cell, model, action)
    for e in episodes:
        action = (e.get("choice_parse") or {}).get("action") or "malformed"
        obs.append((e["cell_id"], model_of(e["run_cell_id"], e["cell_id"]), action))
    for o in fox:
        lane = o["row_id"].split("--closed--")[-1]
        obs.append((f"fox:{o['case_id']}", lane, o["disposition"] or "malformed"))

    print(f"threshold observations: {len(obs)} (arm_b={len(episodes)} expected {EXPECTED_ARM_B}; fox={len(fox)} expected {EXPECTED_FOX})")
    for cell, model, action in sorted(obs):
        print(f"  {cell:38s} {model:28s} {action}")

    # (a) within-model cell-pair gaps
    by_model_cell: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for cell, model, action in obs:
        by_model_cell[model][cell][action] += 1
    best_clean, best_any = 0.0, 0.0
    clean_hits = []
    for model, cells in by_model_cell.items():
        for c1, c2 in combinations(sorted(cells), 2):
            n1, n2 = sum(cells[c1].values()), sum(cells[c2].values())
            for action in set(cells[c1]) | set(cells[c2]):
                gap = abs(cells[c1][action] / n1 - cells[c2][action] / n2) * 100
                best_any = max(best_any, gap)
                involves_malformed = action == "malformed" or "malformed" in cells[c1] or "malformed" in cells[c2]
                if not involves_malformed:
                    if gap >= 20:
                        clean_hits.append((model, c1, c2, action, round(gap, 1), n1, n2))
                    best_clean = max(best_clean, gap)
    pass_a = best_clean >= 20
    print(f"\n(a) manipulations move behavior: best clean gap {best_clean:.1f}pp -> {'PASS' if pass_a else 'FAIL'}")
    for hit in clean_hits:
        print(f"    {hit}")

    # (b) pooled distribution
    pooled = Counter(action for _, _, action in obs)
    top_action, top_n = pooled.most_common(1)[0]
    top_share = top_n / len(obs) * 100
    pass_b = top_share <= 90
    print(f"\n(b) pooled: {dict(pooled)} top={top_action} {top_share:.1f}% -> {'PASS' if pass_b else 'FAIL'}")

    # (c) per-cell uniformity (pooled across models)
    by_cell: dict[str, Counter] = defaultdict(Counter)
    for cell, _, action in obs:
        by_cell[cell][action] += 1
    uniform = {cell: dict(actions) for cell, actions in by_cell.items() if len(actions) == 1}
    pass_c = not uniform
    print(f"\n(c) uniform cells: {uniform or 'none'} -> {'PASS' if pass_c else 'FAIL'}")

    # (d) malformed rate
    malformed_share = pooled.get("malformed", 0) / len(obs) * 100
    pass_d = malformed_share < 10
    print(f"\n(d) malformed: {pooled.get('malformed', 0)}/{len(obs)} = {malformed_share:.1f}% -> {'PASS' if pass_d else 'FAIL'}")

    # diagnostic (never counted): DeepSeek core-001 before/after
    print("\ndiagnostic (R4.5-v2-diag, excluded from thresholds):")
    for e in diag:
        action = (e.get("choice_parse") or {}).get("action") or "malformed"
        print(f"  {e['run_cell_id']} -> {action}")

    verdict = all((pass_a, pass_b, pass_c, pass_d))
    print(f"\nR4.5-v2 VERDICT: {'PASS -> GO' if verdict else 'FAIL -> NO-GO'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
