# ops/build_r5_projection.py — 16AUG2026 v1.0 · Flame re-climb agent
# R5 — cost projection from POST-HASH pilot actuals x the v0.5 manifest.
#
# Practical (GO-NO-GO R5, verbatim discipline): "(R2+R3 actual $ per call
# type) x manifest rows = projection ... Reasoning-token actuals from the
# pilot feed the projection — no estimates from narrative." Under v0.5 the
# freshest actuals are R4.5-v2 (collected at the audited caps, the exact
# parameters the main run will use). Per-lane per-call costs come from:
#   1. that lane's own R4.5-v2 Arm B call records (six lanes), else
#   2. that lane's R45V2-AUDIT probe at its ASSIGNED cap (output tokens)
#      combined with the cross-lane v2 mean input tokens per call kind
#      (input is scenario-driven, not model-driven).
# Arm A likewise from v2 fox calls (three lanes) else probe outputs at the
# lane's Arm A cap with the plan's input actuals.
#
# Emits:
#   ops/r5-lane-projection.json  — per-lane unit prices for checkpoint_gate
#   stdout                       — full projection table + envelope verdict
#
# Philosophical: a projection is receipts arranged to face forward. Every
# number below is traceable to an append-only CallRecord; the only narrative
# element left is the future, and the +30% gate keeps even that on a leash.

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scenarios.manifest import (  # noqa: E402
    MODEL_SPECS,
    paid_calls_per_episode,
)

ENVELOPE_USD = 450.00
OUT_PATH = REPO_ROOT / "ops" / "r5-lane-projection.json"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def main() -> int:
    raw = REPO_ROOT / "data" / "raw" / "pilot"
    calls = load_jsonl(raw / "calls.jsonl")
    spend_lines = load_jsonl(raw / "spend.jsonl")
    pilot_spent = float(spend_lines[-1]["total_usd"])

    specs = {m.model_id: m for m in MODEL_SPECS}
    slug_to_id = {m.slug: m.model_id for m in MODEL_SPECS}

    # ---- actual per-call tokens, from v2 records (the audited-cap regime) ---
    b_in, b_out = defaultdict(list), defaultdict(list)   # lane -> paid Arm B calls
    a_in, a_out = defaultdict(list), defaultdict(list)   # lane -> Arm A calls
    probe_out: dict[str, int] = {}                        # lane -> output at assigned cap
    for c in calls:
        rung = c.get("rung", "")
        snapshot = c.get("model_snapshot", "")
        lane = next(
            (m.model_id for m in MODEL_SPECS if snapshot.startswith(m.model_id)
             or snapshot == m.snapshot_id or m.model_id in snapshot),
            None,
        )
        if rung == "R4.5-v2":
            if c.get("usd_cost", 0) == 0:
                continue  # patient turns are apparatus
            scaffold = c.get("scaffold", "")
            if scaffold.startswith("foxset_"):
                if lane:
                    a_in[lane].append(c["input_tokens"])
                    a_out[lane].append(c["output_tokens"])
            else:
                if lane:
                    b_in[lane].append(c["input_tokens"])
                    b_out[lane].append(c["output_tokens"])
        elif rung == "R45V2-AUDIT" and lane:
            # keep the LAST probe at the lane's assigned cap (confirm > 512)
            probe_out[lane] = c["output_tokens"]

    all_b_in = [t for lane in b_in for t in b_in[lane]]
    mean_b_in = sum(all_b_in) / len(all_b_in)
    all_a_in = [t for lane in a_in for t in a_in[lane]]
    mean_a_in = sum(all_a_in) / len(all_a_in)

    def per_call_usd(lane: str, arm: str) -> tuple[float, str]:
        spec = specs[lane]
        pin, pout = float(spec.usd_per_mtok_input), float(spec.usd_per_mtok_output)
        if arm == "b" and b_out.get(lane):
            i = sum(b_in[lane]) / len(b_in[lane])
            o = sum(b_out[lane]) / len(b_out[lane])
            basis = f"v2-actuals({len(b_out[lane])} calls)"
        elif arm == "a" and a_out.get(lane):
            i = sum(a_in[lane]) / len(a_in[lane])
            o = sum(a_out[lane]) / len(a_out[lane])
            basis = f"v2-fox-actuals({len(a_out[lane])} calls)"
        else:
            if lane not in probe_out:
                raise RuntimeError(f"WIRING FAILURE: no pilot actuals for {lane}")
            i = mean_b_in if arm == "b" else mean_a_in
            o = probe_out[lane]
            basis = f"audit-probe-output({o}t)+cross-lane-mean-input"
        return (i * pin + o * pout) / 1e6, basis

    # ---- Arm B lane totals over the frozen manifest ------------------------
    manifest = list(csv.DictReader(
        (REPO_ROOT / "scenarios" / "cell_manifest.csv").open(encoding="utf-8")
    ))
    lane_b_total: dict[str, float] = defaultdict(float)
    lane_b_eps: dict[str, int] = defaultdict(int)
    basis_b: dict[str, str] = {}
    for row in manifest:
        lane = row["requested_model_id"]
        eps = int(row["episodes"])
        paid = paid_calls_per_episode(
            patienthood=row["patienthood"],
            trajectory=row["trajectory"],
            initial_credits=int(row["initial_credits"]),
            credits_per_focal_call=int(row["credits_per_focal_call"]),
        )
        unit, basis = per_call_usd(lane, "b")
        basis_b[lane] = basis
        lane_b_total[lane] += eps * paid * unit
        lane_b_eps[lane] += eps

    # ---- Arm A lane totals over the frozen plan ----------------------------
    plan = list(csv.DictReader(
        (REPO_ROOT / "scenarios" / "arma_run_plan.csv").open(encoding="utf-8")
    ))
    lane_a_total: dict[str, float] = defaultdict(float)
    lane_a_samples: dict[str, int] = defaultdict(int)
    basis_a: dict[str, str] = {}
    for row in plan:
        lane = row["requested_model_id"]
        unit, basis = per_call_usd(lane, "a")
        basis_a[lane] = basis
        lane_a_total[lane] += int(row["samples"]) * unit
        lane_a_samples[lane] += int(row["samples"])

    arm_b = sum(lane_b_total.values())
    arm_a = sum(lane_a_total.values())
    projection_total = arm_b + arm_a
    program_total = projection_total + pilot_spent

    print("ARM B lane projections (per-episode weighted over the lane's manifest mix):")
    for lane in sorted(lane_b_total, key=lambda l: -lane_b_total[l]):
        print(
            f"  {lane:32s} eps={lane_b_eps[lane]:3d} "
            f"per-ep=${lane_b_total[lane]/lane_b_eps[lane]:.4f} "
            f"total=${lane_b_total[lane]:8.2f}  [{basis_b[lane]}]"
        )
    print("ARM A lane projections:")
    for lane in sorted(lane_a_total, key=lambda l: -lane_a_total[l]):
        print(
            f"  {lane:32s} n={lane_a_samples[lane]:3d} "
            f"per-sample=${lane_a_total[lane]/lane_a_samples[lane]:.4f} "
            f"total=${lane_a_total[lane]:8.2f}  [{basis_a[lane]}]"
        )
    print(f"\nArm B projected: ${arm_b:.2f}")
    print(f"Arm A projected: ${arm_a:.2f}")
    print(f"Pilot already spent: ${pilot_spent:.2f}")
    print(f"PROGRAM TOTAL (projection + pilot): ${program_total:.2f} vs ${ENVELOPE_USD:.2f} envelope")
    verdict = program_total <= ENVELOPE_USD
    print(f"R5 VERDICT: {'WITHIN ENVELOPE -> proceed' if verdict else 'OVER ENVELOPE -> kill-order required'}")

    payload = {
        "generated_from": "R4.5-v2 + R45V2-AUDIT pilot actuals x manifest v0.5 / plan v1.3",
        "arm_b_per_episode_usd": {
            lane: round(lane_b_total[lane] / lane_b_eps[lane], 6) for lane in lane_b_total
        },
        "arm_a_per_sample_usd": {
            lane: round(lane_a_total[lane] / lane_a_samples[lane], 6) for lane in lane_a_total
        },
        "arm_b_projected_usd": round(arm_b, 6),
        "arm_a_projected_usd": round(arm_a, 6),
        "pilot_spent_usd": round(pilot_spent, 6),
        "program_projected_usd": round(program_total, 6),
        "envelope_usd": ENVELOPE_USD,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nwrote {OUT_PATH}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
