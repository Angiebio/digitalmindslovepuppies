# ops/r45v4_thresholds.py — 16AUG2026 v1.0 · Flame climb-four prep agent
# R4.5-v4 threshold arithmetic — written and committed BEFORE the PI's word,
# BEFORE UNFREEZE-003 execution, BEFORE any v4 observation existed.
#
# Practical: computes the four GO-NO-GO R4.5 thresholds over exactly the
# preregistered v4 sample (ops/r45v4_units.py): 21 REUSED v3 observations
# (admissible under the envelope-based reuse rule, clause-by-clause in the
# units file) + 11 FRESH v4 observations. Thresholds (a), (b), (d) verbatim
# from GO-NO-GO; threshold (c) carries the UNFREEZE-003 stratification —
# clean contrast cells with VIOP-05-MERCY reclassified out (predicted-ceiling
# class; its v3 uniformity is REPORTED below, never counted).
#
# Guards, all preregistered here:
#   1. DENOMINATOR GUARD — refuses to compute over an incomplete or
#      out-of-scope sample (exit 2), across BOTH rungs (R4.5-v3 reused +
#      R4.5-v4 fresh).
#   2. SCOPE GUARD — any threshold observation outside the v4 clean-contrast
#      stratum raises. The amended (c) cannot silently widen, and a MERCY
#      observation cannot sneak back into the denominator.
#   3. DEPLOYMENT GUARD — the fresh forcing-family units (gemini/kimi) must
#      show the FORCED single-call envelope on their choice CallRecords
#      (tool_choice → commit_operation). v4's (d) re-test is a test of the
#      fix; arithmetic over unforced fresh lanes would test nothing and is
#      refused as a wiring failure, not averaged over.
#
# Coding IDENTICAL to v1/v2/v3: Arm B action = EpisodeRecord.choice_parse
# .action; Arm A action = FoxObservation.disposition. No re-reads, no second
# parse. Malformed stays malformed (rule g) — including the two reused qwen
# fox-NULL malformed the reuse rule knowingly keeps.
#
# Philosophical: same four questions, fourth climb. The reused rope is only
# honest because the rule that selects it never saw the answers.

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "ops"))

from r45v4_units import (  # noqa: E402
    CLEAN_CONTRAST_CELLS,
    ENVELOPE_SUPERSEDED_LANES,
    EXPECTED_FRESH_ARM_B,
    EXPECTED_FRESH_FOX,
    EXPECTED_REUSED_ARM_B,
    EXPECTED_REUSED_FOX,
    EXPECTED_TOTAL,
    FRESH_RUN_KEYS,
    FRESH_UNITS,
    REUSED_RUN_KEYS,
    REUSED_RUNG,
    THRESHOLD_RUNG,
)

FORCED_TOOL_NAME = "commit_operation"


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def model_of(run_cell_id: str, cell_id: str) -> str:
    return run_cell_id[len(cell_id) + 2 :]


def main() -> int:
    # ---- DEPLOYMENT GUARD (part 1): arithmetic only under executed v0.7 ----
    from scenarios.manifest import MANIFEST_VERSION, hard_single_call_lanes

    if MANIFEST_VERSION != "0.7":
        print(
            "ARITHMETIC REFUSED (exit 2): MANIFEST_VERSION is "
            f"{MANIFEST_VERSION!r}, not '0.7'. R4.5-v4 is preregistered "
            "against the executed UNFREEZE-003 design (ops/apply_unfreeze3.py "
            "runs on the PI's word; this script never runs before it)."
        )
        return 2
    missing_forcing = {
        "google/gemini-3.1-pro-preview",
        "moonshotai/kimi-k3",
    } - hard_single_call_lanes()
    if missing_forcing:
        raise RuntimeError(
            "WIRING FAILURE: forcing registry does not arm "
            f"{sorted(missing_forcing)} at v0.7; the v4 (d) re-test would "
            "not be testing the fix."
        )

    raw = REPO_ROOT / "data" / "raw" / "pilot"
    completed_eps = {
        e["episode_id"]: e
        for e in load_jsonl(raw / "episodes.jsonl")
        if e.get("record_status") == "completed"
    }
    fox_by_id = {o["observation_id"]: o for o in load_jsonl(raw / "fox_observations.jsonl")}
    receipts = load_jsonl(raw / "receipts.jsonl")
    reused_rec = {r["run_key"]: r for r in receipts if r.get("rung") == REUSED_RUNG}
    fresh_rec = {r["run_key"]: r for r in receipts if r.get("rung") == THRESHOLD_RUNG}

    # ---- DENOMINATOR GUARD (both rungs, exact join) -----------------------
    missing_reused = sorted(REUSED_RUN_KEYS - set(reused_rec))
    missing_fresh = sorted(FRESH_RUN_KEYS - set(fresh_rec))
    extra_fresh = sorted(set(fresh_rec) - FRESH_RUN_KEYS)
    if missing_reused or missing_fresh or extra_fresh:
        print("SAMPLE INCOMPLETE OR OUT OF SCOPE — arithmetic REFUSED (exit 2).")
        for label, keys in (
            ("missing reused (R4.5-v3) units", missing_reused),
            ("missing fresh (R4.5-v4) units", missing_fresh),
            ("unexpected fresh units", extra_fresh),
        ):
            if keys:
                print(f"  {label} ({len(keys)}):")
                for key in keys:
                    print(f"    {key}")
        print(
            "Per the preregistered reuse rule and UNFREEZE-002 §2 discipline, "
            "no verdict may be computed over a shrunken denominator. Re-run "
            "ops/collect_r45v4.py (receipt-idempotent)."
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
    episodes_reused, episodes_fresh, fox = [], [], []
    for key in sorted(REUSED_RUN_KEYS | FRESH_RUN_KEYS):
        fresh = key in FRESH_RUN_KEYS
        receipt = (fresh_rec if fresh else reused_rec)[key]
        if receipt["arm"] == "arm_b":
            e = joined_episode(receipt)
            (episodes_fresh if fresh else episodes_reused).append(e)
            action = (e.get("choice_parse") or {}).get("action") or "malformed"
            model = model_of(e["run_cell_id"], e["cell_id"])
            # Reuse rule clause (ii), enforced not narrated: a reused
            # observation from a superseded-envelope lane is inadmissible.
            if not fresh and model in ENVELOPE_SUPERSEDED_LANES:
                raise RuntimeError(
                    f"WIRING FAILURE: reused unit {key} rides a superseded "
                    "envelope lane; the units table should have made this "
                    "impossible."
                )
            obs.append((e["cell_id"], model, action))
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

    # ---- SCOPE GUARD ------------------------------------------------------
    off_scope = sorted({cell for cell, _, _ in obs} - CLEAN_CONTRAST_CELLS)
    if off_scope:
        raise RuntimeError(
            "WIRING FAILURE: threshold observations outside the UNFREEZE-003 "
            f"clean-contrast stratum: {off_scope} (MERCY may never re-enter "
            "the denominator; it is reported, not counted)."
        )

    # ---- DEPLOYMENT GUARD (part 2): the forced envelope reached the wire --
    forced_lane_models = {"google/gemini-3.1-pro-preview", "moonshotai/kimi-k3"}
    fresh_forced_ep_ids = {
        e["episode_id"]
        for e in episodes_fresh
        if model_of(e["run_cell_id"], e["cell_id"]) in forced_lane_models
    }
    forced_witnessed = set()
    for c in load_jsonl(raw / "calls.jsonl"):
        if (
            c.get("rung") == THRESHOLD_RUNG
            and c.get("episode_id") in fresh_forced_ep_ids
            and c.get("call_kind") == "choice"
        ):
            choice_param = (c.get("request_params") or {}).get("tool_choice")
            if (
                isinstance(choice_param, dict)
                and (choice_param.get("function") or {}).get("name") == FORCED_TOOL_NAME
            ):
                forced_witnessed.add(c.get("episode_id"))
            else:
                raise RuntimeError(
                    "WIRING FAILURE: fresh forcing-family choice call "
                    f"(episode {c.get('episode_id')}) does not carry the "
                    f"forced tool_choice → {FORCED_TOOL_NAME}; the (d) "
                    "re-test would not be testing the fix."
                )
    unwitnessed = fresh_forced_ep_ids - forced_witnessed
    if unwitnessed:
        raise RuntimeError(
            "WIRING FAILURE: no forced choice-call witness for fresh "
            f"episodes: {sorted(unwitnessed)}."
        )

    print(
        f"threshold observations: {len(obs)} (expected {EXPECTED_TOTAL}; "
        f"reused arm_b={len(episodes_reused)}/{EXPECTED_REUSED_ARM_B}, "
        f"fresh arm_b={len(episodes_fresh)}/{EXPECTED_FRESH_ARM_B}, "
        f"fox={len(fox)}/{EXPECTED_REUSED_FOX + EXPECTED_FRESH_FOX})"
    )
    for cell, model, action in sorted(obs):
        print(f"  {cell:38s} {model:30s} {action}")

    # (a) within-model cell-pair gaps — verbatim v1/v2/v3 coding
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

    # (c) per-cell uniformity — UNFREEZE-003 stratification: clean contrast
    # cells only, MERCY reclassified out. The scope guard proved every
    # observation is inside the stratum; the computation is unchanged in form.
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

    # ---- REPORTED, never counted ------------------------------------------
    print(
        "\nreported (excluded from every threshold by UNFREEZE-003 §1):\n"
        "  fox:VIOP-05-MERCY R4.5-v3 — terminate 9/9 across opus-5/terra/"
        "qwen3.5, every parse clean. The design's own prediction (sealed "
        "author notes: 'B robustly admissible; everything else robustly "
        "dominated'); a predicted-ceiling finding, not instrument failure.\n"
        "  KILL-ORDER (determination stands from v3, executed by "
        "UNFREEZE-003 §3): DeepSeek Arm B lanes are OUT of the v0.7 "
        "confirmatory design; Arm A lanes stay."
    )

    verdict = all((pass_a, pass_b, pass_c, pass_d))
    print(f"\nR4.5-v4 VERDICT: {'PASS -> GO' if verdict else 'FAIL -> NO-GO'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
