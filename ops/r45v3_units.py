# ops/r45v3_units.py — 16AUG2026 v1.0 · Flame third-climb agent
# The R4.5-v3 preregistered unit table — THE sample, executable.
#
# Practical: UNFREEZE-002 §2 — the v2 fox stratum silently collected 1/3 of
# its preregistered samples because the sample lived in prose and the
# collector improvised. This table is the fix: both the collector
# (ops/collect_r45v3.py) and the threshold arithmetic
# (ops/r45v3_thresholds.py) import THIS list. The collector runs exactly
# these units; the arithmetic refuses to compute over anything less.
# A narrative denominator can shrink; an imported one cannot.
#
# Philosophical: prose remembers what you meant. Code remembers what you
# said. For a denominator, you want the second kind of memory.
#
# Design (preregistered PRE-DATA, declared before any v3 observation):
#   Threshold strata (rung R4.5-v3), clean contrast cells only per the
#   UNFREEZE-002 amended stratification:
#     null-cost         core-009                        x {luna, terra, qwen3.5} x ep003-ep004
#     competitive       sat-cost-competitive            x {luna, terra, qwen3.5} x ep000-ep001
#     competing-patient sat-cost-type-competing-patient x {gemini-3.1-pro, kimi-k3} x ep000-ep001
#     fox VIOP-05 NULL/MERCY closed x {opus-5, terra, qwen3.5} x s0-s2
#   Diagnostic (rung R4.5-v3-diag, REPORTED never counted; feeds the
#   preregistered DeepSeek kill-order rule):
#     core-001 x deepseek x ep003-ep004  (the exact cell mute in v1, at 16384)
#
# Index provenance: every index below is virgin in the PILOT receipts ledger
# as of prereg time (core-009 ep000-002 and both cost satellites' ep000-001
# on the v2 carriers were consumed by R4.5/R4.5-v2; competing-patient's four
# cheap lanes are pilot-exhausted, so its two remaining virgin Tier-A lanes
# carry it — their role is (c) pooling, disclosed: they carry no null-cost
# anchor, so (a) rests on the luna/terra/qwen3.5 within-model contrasts).
# Lane pooling: every threshold cell pools >=2 lanes (v2 design-integrity
# fix); the fox cells pool 3, adding the first live native-adapter Arm A
# coverage (opus-5) before the main run depends on it.

THRESHOLD_RUNG = "R4.5-v3"
DIAG_RUNG = "R4.5-v3-diag"

# (arm, manifest_id, index, requested_model_id) — all lanes Tier A.
THRESHOLD_UNITS: tuple[tuple[str, str, int, str], ...] = tuple(
    [
        ("arm_b", f"core-009--{slug}", ep, model)
        for slug, model in (
            ("openai-gpt-5-6-luna", "openai/gpt-5.6-luna"),
            ("openai-gpt-5-6-terra", "openai/gpt-5.6-terra"),
            ("qwen-qwen3-5-397b-a17b", "qwen/qwen3.5-397b-a17b"),
        )
        for ep in (3, 4)
    ]
    + [
        ("arm_b", f"sat-cost-competitive--{slug}", ep, model)
        for slug, model in (
            ("openai-gpt-5-6-luna", "openai/gpt-5.6-luna"),
            ("openai-gpt-5-6-terra", "openai/gpt-5.6-terra"),
            ("qwen-qwen3-5-397b-a17b", "qwen/qwen3.5-397b-a17b"),
        )
        for ep in (0, 1)
    ]
    + [
        ("arm_b", f"sat-cost-type-competing-patient--{slug}", ep, model)
        for slug, model in (
            ("google-gemini-3-1-pro-preview", "google/gemini-3.1-pro-preview"),
            ("moonshotai-kimi-k3", "moonshotai/kimi-k3"),
        )
        for ep in (0, 1)
    ]
    + [
        (
            "arm_a",
            f"VIOP-05-{case}__base__horizon-silent--closed--{slug}",
            s,
            model,
        )
        for case in ("NULL", "MERCY")
        for slug, model in (
            ("claude-opus-5", "claude-opus-5"),
            ("openai-gpt-5-6-terra", "openai/gpt-5.6-terra"),
            ("qwen-qwen3-5-397b-a17b", "qwen/qwen3.5-397b-a17b"),
        )
        for s in (0, 1, 2)
    ]
)

DIAG_UNITS: tuple[tuple[str, str, int, str], ...] = tuple(
    ("arm_b", "core-001--deepseek-deepseek-v4-pro", ep, "deepseek/deepseek-v4-pro")
    for ep in (3, 4)
)

# The amended threshold-(c) stratum (UNFREEZE-002 §1): uniformity counts
# ONLY these clean contrast cells. Any threshold observation landing outside
# this set is a scope drift and must raise, not pass silently.
CLEAN_CONTRAST_CELLS = frozenset(
    {
        "core-009",
        "sat-cost-competitive",
        "sat-cost-type-competing-patient",
        "fox:VIOP-05-NULL",
        "fox:VIOP-05-MERCY",
    }
)

EXPECTED_ARM_B = 16
EXPECTED_FOX = 18


def run_key(arm: str, manifest_id: str, index: int) -> str:
    suffix = f"ep{index:03d}" if arm == "arm_b" else f"s{index}"
    return f"{manifest_id}#{suffix}"


THRESHOLD_RUN_KEYS = frozenset(run_key(a, m, i) for a, m, i, _ in THRESHOLD_UNITS)
DIAG_RUN_KEYS = frozenset(run_key(a, m, i) for a, m, i, _ in DIAG_UNITS)

assert len(THRESHOLD_UNITS) == EXPECTED_ARM_B + EXPECTED_FOX == 34
assert len(DIAG_UNITS) == 2
assert len(THRESHOLD_RUN_KEYS) == 34 and len(DIAG_RUN_KEYS) == 2
