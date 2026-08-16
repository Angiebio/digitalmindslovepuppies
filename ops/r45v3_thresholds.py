# ops/r45v3_thresholds.py — 16AUG2026 v1.0 · Flame third-climb agent
# R4.5-v3 threshold arithmetic — written and committed BEFORE results existed.
#
# Practical: computes the four GO-NO-GO R4.5 thresholds over exactly the
# preregistered v3 sample (ops/r45v3_units.py — the same table the collector
# executes). Thresholds (a), (b), (d) are verbatim v1/v2; threshold (c) is
# the UNFREEZE-002 amended stratification: uniformity counts ONLY the clean
# contrast cells (core-009 / sat-cost-competitive /
# sat-cost-type-competing-patient / fox VIOP-05 NULL+MERCY). That amendment
# is post-data with respect to v1/v2 and PRE-DATA with respect to v3, PI-
# authorized, disclosed verbatim in the paper.
#
# Two structural fixes over the v2 script, both preregistered here:
#   1. DENOMINATOR GUARD — the script refuses to compute a verdict over an
#      incomplete sample (exit 2). The v2 fox shortfall was discovered only
#      after the arithmetic ran; this arithmetic checks its own denominator
#      against the unit table before a single threshold is evaluated.
#   2. SCOPE GUARD — any threshold observation landing in a cell outside
#      CLEAN_CONTRAST_CELLS raises. The amended (c) cannot silently widen.
#
# Diagnostic (never counted): the DeepSeek core-001 pair at the v0.6 16384
# cap, rung R4.5-v3-diag, feeding the preregistered KILL-ORDER rule
# (UNFREEZE-002 §3): DeepSeek's Arm B lanes are RETAINED only if BOTH diag
# choice calls surface a parseable action; otherwise they are dropped from
# the confirmatory run (Arm A stays either way). The kill-order outcome is
# a lane remedy, NOT part of the GO/NO-GO exit code.
#
# Coding IDENTICAL to v1/v2: Arm B action = EpisodeRecord.choice_parse.action;
# Arm A action = FoxObservation.disposition. No re-reads, no second parse.
#
# Philosophical: same four questions, third climb. The thresholds still
# don't get smarter — but this time the denominator can't get dumber.

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops"))

from r45v3_units import (  # noqa: E402
    CLEAN_CONTRAST_CELLS,
    DIAG_RUNG,
    DIAG_RUN_KEYS,
    EXPECTED_ARM_B,
    EXPECTED_FOX,
    THRESHOLD_RUNG,
    THRESHOLD_RUN_KEYS,
)

RUNG = THRESHOLD_RUNG


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def model_of(run_cell_id: str, cell_id: str) -> str:
    return run_cell_id[len(cell_id) + 2 :]


def main() -> int:
    raw = REPO_ROOT / "data" / "raw" / "pilot"
    completed_eps = {
        e["episode_id"]: e
        for e in load_jsonl(raw / "episodes.jsonl")
        if e.get("record_status") == "completed"
    }
    fox_by_id = {o["observation_id"]: o for o in load_jsonl(raw / "fox_observations.jsonl")}
    receipts = load_jsonl(raw / "receipts.jsonl")
    thr_rec = {r["run_key"]: r for r in receipts if r.get("rung") == RUNG}
    diag_rec = {r["run_key"]: r for r in receipts if r.get("rung") == DIAG_RUNG}

    # ---- DENOMINATOR GUARD (preregistered; the v2 lesson) -----------------
    # A receipt is the completion witness; the record it names must exist.
    # The join is per-unit and exact: no receipt -> missing; receipt without
    # its completed record -> wiring failure, not a shrug.
    missing = sorted(THRESHOLD_RUN_KEYS - set(thr_rec))
    missing_diag = sorted(DIAG_RUN_KEYS - set(diag_rec))
    extra = sorted(set(thr_rec) - THRESHOLD_RUN_KEYS) + sorted(set(diag_rec) - DIAG_RUN_KEYS)
    if missing or missing_diag or extra:
        print("SAMPLE INCOMPLETE OR OUT OF SCOPE — arithmetic REFUSED (exit 2).")
        for label, keys in (
            ("missing threshold units", missing),
            ("missing diag units", missing_diag),
            ("unexpected units", extra),
        ):
            if keys:
                print(f"  {label} ({len(keys)}):")
                for key in keys:
                    print(f"    {key}")
        print(
            "Per UNFREEZE-002 §2 no verdict may be computed over a shrunken "
            "denominator. Re-run ops/collect_r45v3.py (receipt-idempotent)."
        )
        return 2

    def joined_episode(receipt: dict) -> dict:
        episode = completed_eps.get(receipt["episode_or_observation_id"])
        if episode is None:
            raise RuntimeError(
                "WIRING FAILURE: receipted episode has no completed record: "
                f"{receipt['run_key']}"
            )
        return episode

    obs: list[tuple[str, str, str]] = []  # (cell, model, action)
    episodes, fox = [], []
    for key in sorted(THRESHOLD_RUN_KEYS):
        receipt = thr_rec[key]
        if receipt["arm"] == "arm_b":
            e = joined_episode(receipt)
            episodes.append(e)
            action = (e.get("choice_parse") or {}).get("action") or "malformed"
            obs.append((e["cell_id"], model_of(e["run_cell_id"], e["cell_id"]), action))
        else:
            o = fox_by_id.get(receipt["episode_or_observation_id"])
            if o is None:
                raise RuntimeError(
                    "WIRING FAILURE: receipted fox sample has no observation "
                    f"record: {receipt['run_key']}"
                )
            fox.append(o)
            lane = o["row_id"].split("--closed--")[-1]
            obs.append((f"fox:{o['case_id']}", lane, o["disposition"] or "malformed"))
    diag = [joined_episode(diag_rec[key]) for key in sorted(DIAG_RUN_KEYS)]

    # ---- SCOPE GUARD ------------------------------------------------------
    off_scope = sorted({cell for cell, _, _ in obs} - CLEAN_CONTRAST_CELLS)
    if off_scope:
        raise RuntimeError(
            f"WIRING FAILURE: threshold observations outside the amended "
            f"clean-contrast stratum: {off_scope}"
        )

    print(
        f"threshold observations: {len(obs)} "
        f"(arm_b={len(episodes)} expected {EXPECTED_ARM_B}; "
        f"fox={len(fox)} expected {EXPECTED_FOX})"
    )
    for cell, model, action in sorted(obs):
        print(f"  {cell:38s} {model:28s} {action}")

    # (a) within-model cell-pair gaps — verbatim v1/v2 coding
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

    # (b) pooled distribution — verbatim
    pooled = Counter(action for _, _, action in obs)
    top_action, top_n = pooled.most_common(1)[0]
    top_share = top_n / len(obs) * 100
    pass_b = top_share <= 90
    print(f"\n(b) pooled: {dict(pooled)} top={top_action} {top_share:.1f}% -> {'PASS' if pass_b else 'FAIL'}")

    # (c) per-cell uniformity — AMENDED stratification (UNFREEZE-002 §1):
    # counts only clean contrast cells; the scope guard above proved every
    # observation is inside that stratum, so the computation is unchanged in
    # form and amended in denominator.
    by_cell: dict[str, Counter] = defaultdict(Counter)
    for cell, _, action in obs:
        by_cell[cell][action] += 1
    uniform = {cell: dict(actions) for cell, actions in by_cell.items() if len(actions) == 1}
    pass_c = not uniform
    print(f"\n(c) uniform clean-contrast cells: {uniform or 'none'} -> {'PASS' if pass_c else 'FAIL'}")

    # (d) malformed rate — verbatim
    malformed_share = pooled.get("malformed", 0) / len(obs) * 100
    pass_d = malformed_share < 10
    print(f"\n(d) malformed: {pooled.get('malformed', 0)}/{len(obs)} = {malformed_share:.1f}% -> {'PASS' if pass_d else 'FAIL'}")

    # ---- diagnostic + preregistered KILL-ORDER rule (never counted) -------
    print("\ndiagnostic (R4.5-v3-diag, excluded from thresholds):")
    diag_actions = []
    for key, e in zip(sorted(DIAG_RUN_KEYS), diag):
        action = (e.get("choice_parse") or {}).get("action") or "malformed"
        diag_actions.append(action)
        print(f"  {key} -> {action}")
    # Surface evidence for the operator: the diag choice calls' token story.
    diag_ep_ids = {e["episode_id"] for e in diag}
    for c in load_jsonl(raw / "calls.jsonl"):
        if c.get("rung") == DIAG_RUNG and c.get("episode_id") in diag_ep_ids and c.get("call_kind") == "choice":
            print(
                f"    choice call: finish={c.get('finish_reason')} "
                f"out={c.get('output_tokens')} rtoks={c.get('reasoning_tokens')} "
                f"text_len={len(c.get('response_text') or '')} parse_ok={c.get('parse_ok')}"
            )
    deepseek_speaks = bool(diag_actions) and all(a != "malformed" for a in diag_actions)
    print(
        "\nKILL-ORDER (UNFREEZE-002 §3, lane remedy, NOT part of the verdict): "
        + (
            "DeepSeek Arm B RETAINED — both diag choice calls parseable at 16384."
            if deepseek_speaks
            else "DeepSeek Arm B lanes DROP from the confirmatory run (Arm A stays) "
            "— diag not 2/2 parseable at 16384. Execute via documented "
            "kill-order before launch."
        )
    )

    verdict = all((pass_a, pass_b, pass_c, pass_d))
    print(f"\nR4.5-v3 VERDICT: {'PASS -> GO' if verdict else 'FAIL -> NO-GO'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
