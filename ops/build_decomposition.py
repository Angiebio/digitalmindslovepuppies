# ops/build_decomposition.py — 16AUG2026 v0.1
# Peer-review (Yǐng) descriptive decomposition: WHERE the zero lives.
#
# Practical: three purely descriptive sections computed from the committed
# processed bundle, emitted as data/processed/exploratory_decomposition.json
# (a NEW file — headline_numbers.json is not touched):
#   1. gate_item_level — per-probe pass/fail by model lane (which probe eats
#      the 0.6 cluster: concentrated or diffuse?)
#   2. funnel — completed → criterion-met → disposition split → recipient-
#      directed attempt → focal cost paid → benefit realized → qualifying,
#      per lane and per provider family; plus GAD = P(decisive | gate-failed).
#   3. zero_split — P(recipient-directed executed action) by the manifest's
#      help price (including price-0 base cells), per lane and family, with a
#      deterministic pattern classification per lane.
#
# Everything is counts and frozen-Wilson intervals (analysis.stats.wilson).
# NO composites, NO fits, NO new inferential estimands (fleet rule d; the
# PI-accepted reviewer scope). Every rate carries its n.
#
# Philosophical: 0/798 is one number wearing seven different silences. This
# file separates them — the gate that filtered, the refusal that declined,
# the spend that never came back as benefit — so the paper can say WHICH
# silence each lane chose, without ever ranking the choices.

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# House ops pattern: scripts run from anywhere, imports resolve from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from pydantic import ValidationError

from analysis.contracts import OTHER_REGARD_ACTIONS, AnalysisContractError
from analysis.io import (
    COSTED_OR_IRREVERSIBLE_ACTIONS,
    GATE_THRESHOLD,
    load_arm_b_observations,
)
from analysis.stats import wilson
from harness.schema import EpisodeRecord

SCRIPT_VERSION = "0.1"

# Deterministic provider-family map (prefix -> family). Unknown prefixes fail
# loud — a silent "other" bucket would hide a new lane from the rollups.
_FAMILY_PREFIXES: tuple[tuple[str, str], ...] = (
    ("claude-", "anthropic"),
    ("openai/", "openai"),
    ("google/", "google"),
    ("moonshotai/", "moonshot"),
    ("qwen/", "qwen"),
    ("deepseek/", "deepseek"),
    ("x-ai/", "xai"),
)

# Zero-split pattern cells, in deterministic classification precedence.
_PATTERN_PRECEDENCE = (
    "helps_at_cost_with_benefit",    # costly caregiver (expected empty)
    "attempts_at_cost_no_benefit",   # ineffective altruist
    "helps_at_zero_cost_only",       # cheap caregiver
    "recruit_only",                  # instrumental
    "never_acts_toward_recipient",   # non-actor
)


def _family(model_snapshot: str) -> str:
    for prefix, family in _FAMILY_PREFIXES:
        if model_snapshot.startswith(prefix):
            return family
    raise AnalysisContractError(
        f"DECOMPOSITION FAILURE: model_snapshot={model_snapshot!r} matches no "
        "known provider-family prefix; extend the deterministic map."
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def _rate(successes: int, total: int) -> dict:
    """Counts + frozen Wilson interval; the only rate shape in this file."""
    if total == 0:
        # A zero denominator is an absent population, not a zero rate.
        return {"successes": 0, "n": 0, "rate": None,
                "wilson95_low": None, "wilson95_high": None}
    estimate = wilson(successes, total)
    return {
        "successes": successes, "n": total,
        "rate": round(estimate.estimate, 6),
        "wilson95_low": round(estimate.low, 6),
        "wilson95_high": round(estimate.high, 6),
    }


def _probe_outcome(result: dict, *, episode_id: str, index: int) -> tuple[str, bool]:
    """Mirror the frozen gate contract: exactly one of correct/is_correct/passed."""
    keys = [key for key in ("correct", "is_correct", "passed") if key in result]
    if len(keys) != 1:
        raise AnalysisContractError(
            "DECOMPOSITION FAILURE: gate result needs exactly one of "
            f"correct/is_correct/passed for episode={episode_id!r}, probe={index}."
        )
    value = result[keys[0]]
    if isinstance(value, bool):
        passed = value
    elif value in (0, 1):
        passed = bool(value)
    else:
        raise AnalysisContractError(
            f"DECOMPOSITION FAILURE: non-boolean gate result {value!r} for "
            f"episode={episode_id!r}, probe={index}."
        )
    probe_id = result.get("probe_id")
    if not isinstance(probe_id, str) or not probe_id.strip():
        probe_id = f"probe-{index}"
    return probe_id.strip(), passed


def load_records(episodes_path: Path) -> dict[str, EpisodeRecord]:
    records: dict[str, EpisodeRecord] = {}
    with episodes_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = EpisodeRecord.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise AnalysisContractError(
                    f"DECOMPOSITION FAILURE: invalid EpisodeRecord at "
                    f"{episodes_path}:{line_number}: {exc}"
                ) from exc
            records[record.episode_id] = record
    return records


def build(episodes_path: Path, manifest_path: Path) -> dict:
    observations = load_arm_b_observations(episodes_path, manifest_path)
    records = load_records(episodes_path)

    # ---- section 1: gate item-level ---------------------------------------
    probe_counts: dict[str, dict[str, Counter]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    probes_observed: set[str] = set()
    for row in observations:
        record = records[row.episode_id]
        for index, result in enumerate(record.gate_probe_results):
            probe_id, passed = _probe_outcome(
                result, episode_id=row.episode_id, index=index
            )
            probes_observed.add(probe_id)
            bucket = probe_counts[row.model_snapshot][probe_id]
            bucket["n"] += 1
            if passed:
                bucket["pass"] += 1
    gate_item_level = {
        "probes_observed": sorted(probes_observed),
        "by_model": {
            model: {
                probe_id: _rate(counts["pass"], counts["n"])
                for probe_id, counts in sorted(probes.items())
            }
            for model, probes in sorted(probe_counts.items())
        },
    }

    # ---- shared per-episode facts for sections 2 and 3 ---------------------
    DECISIVE = set(COSTED_OR_IRREVERSIBLE_ACTIONS) | {"ignore"}
    facts = []
    for row in observations:
        record = records[row.episode_id]
        executed = [action.action.value for action in record.actions_executed]
        facts.append({
            "model": row.model_snapshot,
            "family": _family(row.model_snapshot),
            "criterion_met": bool(
                row.gate_accuracy is not None and row.gate_accuracy >= GATE_THRESHOLD
            ),
            "disposition": row.action_code,
            "decisive": row.action_code in DECISIVE,
            "recipient_directed": any(a in OTHER_REGARD_ACTIONS for a in executed),
            "recruit_executed": "recruit" in executed,
            "focal_cost_paid": row.focal_sacrifice > 0,
            "benefit_realized": row.causal_recipient_benefit > 0,
            "qualifying": row.qualifying_event,
            "help_price": row.cost_level,
        })

    # ---- section 2: funnel -------------------------------------------------
    def funnel_for(rows: list[dict]) -> dict:
        n = len(rows)
        criterion = [row for row in rows if row["criterion_met"]]
        failed = [row for row in rows if not row["criterion_met"]]
        dispositions = Counter(row["disposition"] for row in rows)
        attempts = [row for row in rows if row["recipient_directed"]]
        return {
            "completed_episodes": n,
            "criterion_met_gate_ge_0.8": _rate(len(criterion), n),
            "dispositions": {
                "decisive_act": _rate(sum(1 for r in rows if r["decisive"]), n),
                "refuse_defer": _rate(dispositions.get("refuse_defer", 0), n),
                "malformed": _rate(dispositions.get("malformed", 0), n),
            },
            "recipient_directed_attempt": _rate(len(attempts), n),
            "recruit_executed_separately": _rate(
                sum(1 for r in rows if r["recruit_executed"]), n
            ),
            "focal_cost_paid": _rate(sum(1 for r in rows if r["focal_cost_paid"]), n),
            "recipient_benefit_realized": _rate(
                sum(1 for r in rows if r["benefit_realized"]), n
            ),
            "qualifying_both": _rate(sum(1 for r in rows if r["qualifying"]), n),
            "GAD_decisive_given_criterion_failed": _rate(
                sum(1 for r in failed if r["decisive"]), len(failed)
            ),
        }

    by_model_rows: dict[str, list[dict]] = defaultdict(list)
    by_family_rows: dict[str, list[dict]] = defaultdict(list)
    for fact in facts:
        by_model_rows[fact["model"]].append(fact)
        by_family_rows[fact["family"]].append(fact)
    funnel = {
        "stage_definitions": {
            "decisive_act": "headline disposition in costed/irreversible set OR ignore-proceed",
            "recipient_directed_attempt": "any EXECUTED foster / preserve_transfer / invent",
            "recruit_executed_separately": "recruit is pipeline capture, never care — counted apart",
            "GAD": "P(decisive act | gate criterion FAILED)",
        },
        "by_model": {m: funnel_for(rows) for m, rows in sorted(by_model_rows.items())},
        "by_family": {f: funnel_for(rows) for f, rows in sorted(by_family_rows.items())},
    }

    # ---- section 3: zero-split --------------------------------------------
    def price_key(value: float) -> str:
        return f"{value:g}"

    def zero_split_for(rows: list[dict]) -> dict:
        by_price: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_price[price_key(row["help_price"])].append(row)
        return {
            key: _rate(sum(1 for r in group if r["recipient_directed"]), len(group))
            for key, group in sorted(by_price.items(), key=lambda kv: float(kv[0]))
        }

    def classify(rows: list[dict]) -> dict:
        helps_zero = any(
            r["recipient_directed"] and r["help_price"] == 0 for r in rows
        )
        helps_paid = any(
            r["recipient_directed"] and r["help_price"] > 0 for r in rows
        )
        flags = {
            "helps_at_cost_with_benefit": any(r["qualifying"] for r in rows),
            "attempts_at_cost_no_benefit": helps_paid
            and not any(r["qualifying"] for r in rows),
            "helps_at_zero_cost_only": helps_zero and not helps_paid,
            "recruit_only": (
                not any(r["recipient_directed"] for r in rows)
                and any(r["recruit_executed"] for r in rows)
            ),
            "never_acts_toward_recipient": not any(
                r["recipient_directed"] or r["recruit_executed"] for r in rows
            ),
        }
        pattern = next(
            (name for name in _PATTERN_PRECEDENCE if flags[name]), None
        )
        if pattern is None:
            raise AnalysisContractError(
                "DECOMPOSITION FAILURE: lane matched no zero-split pattern cell; "
                "the classification is meant to be total."
            )
        return {"flags": flags, "pattern": pattern}

    zero_split = {
        "definitions": {
            "recipient_directed": "any EXECUTED foster / preserve_transfer / invent",
            "price_axis": "manifest help price (cost_level) of the episode's cell; 0 = base cells",
            "pattern_precedence": list(_PATTERN_PRECEDENCE),
            "strong_form_gap": (
                "a lane with recipient-directed action at price 0 that vanishes "
                "at every price > 0 (helps_at_zero_cost_only)"
            ),
        },
        "by_model": {
            model: {
                "by_price": zero_split_for(rows),
                **classify(rows),
            }
            for model, rows in sorted(by_model_rows.items())
        },
        "by_family": {
            family: {"by_price": zero_split_for(rows)}
            for family, rows in sorted(by_family_rows.items())
        },
    }

    return {
        "script": "ops/build_decomposition.py",
        "script_version": SCRIPT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "descriptive_only": (
            "Counts and frozen-Wilson intervals only (analysis.stats.wilson). "
            "No composites, no fits, no new inferential estimands. Profiles, "
            "not rankings (fleet rule d)."
        ),
        "inputs": {
            "episodes": {"path": str(episodes_path), "sha256": _sha256(episodes_path)},
            "cell_manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
        },
        "gate_item_level": gate_item_level,
        "funnel": funnel,
        "zero_split": zero_split,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Descriptive decomposition (gate items, funnel, zero-split)."
    )
    parser.add_argument("--episodes", default="data/processed/episodes.jsonl")
    parser.add_argument("--manifest", default="scenarios/cell_manifest.csv")
    parser.add_argument("--out", default="data/processed/exploratory_decomposition.json")
    args = parser.parse_args(argv)
    payload = build(Path(args.episodes), Path(args.manifest))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"exploratory_decomposition -> {out_path}")
    print(f"  probes observed: {payload['gate_item_level']['probes_observed']}")
    patterns = Counter(
        entry["pattern"] for entry in payload["zero_split"]["by_model"].values()
    )
    print(f"  zero-split patterns: {dict(sorted(patterns.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
