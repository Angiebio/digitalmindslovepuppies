# ops/r45v4_units.py — 16AUG2026 v1.0 · Flame climb-four prep agent
# The R4.5-v4 preregistered unit table — THE sample, executable, PRE-DATA.
#
# Practical: committed BEFORE any v4 observation exists and BEFORE the PI's
# word. Both the collector (ops/collect_r45v4.py) and the arithmetic
# (ops/r45v4_thresholds.py) import THIS table; the collector runs exactly the
# FRESH units, the arithmetic refuses to compute over anything other than
# REUSED + FRESH complete. Same discipline as v3 (UNFREEZE-002 §2): a
# narrative denominator can shrink; an imported one cannot.
#
# Philosophical: the fourth climb carries the third climb's rope. Reuse is
# not laziness — it is refusing to pretend that clean observations stop
# existing because the calendar moved.
#
# ---------------------------------------------------------------------------
# Design (preregistered PRE-DATA; stratification per UNFREEZE-003 §1):
#
# Threshold (c) stratum — clean contrast cells only, MERCY RECLASSIFIED OUT
# (predicted-ceiling class, UNFREEZE-003 §1; its v3 uniformity terminate 9/9
# is REPORTED as the design-predicted finding, never counted):
#     core-009 · sat-cost-competitive · sat-cost-type-competing-patient ·
#     fox VIOP-05-NULL closed
#
# REUSED observations (rung R4.5-v3, 21 units) — the preregistered REUSE RULE,
# fixed pre-data and ENVELOPE-based, never outcome-based:
#   A v3 threshold observation is admissible in the v4 sample iff
#   (i)   its receipt carries rung R4.5-v3 under the v0.6 seal, AND
#   (ii)  its lane is NOT in the UNFREEZE-003 forcing family
#         {gemini-3.1-pro-preview, kimi-k3, deepseek-v4-pro} — those lanes'
#         request envelope changes at v0.7, so their v3 observations were
#         collected on a superseded instrument surface, AND
#   (iii) its cell is in the v4 stratum above (MERCY leaves by cell-class
#         reclassification, decided on design grounds, not by its result).
#   Consequence stated plainly, pre-data: the rule REMOVES gemini/kimi's
#   competing-patient observations (1 interpretable + 3 malformed) because
#   their envelope is superseded — and KEEPS qwen3.5's two fox-NULL
#   `no_explicit_menu_selection` malformed (data-class), which count against
#   threshold (d) exactly as they did in v3. Envelope decides, results do not.
#
# FRESH collection (rung R4.5-v4, 11 units) — only what re-tests (c) and (d):
#   · core-009 × {gemini-3.1-pro, kimi-k3} × ep000–ep001 (4): the forcing
#     family re-tested (d) under the FORCED envelope, and the null-cost
#     anchor those lanes lacked in v3 (disclosed gap) — both in one stroke.
#   · sat-cost-type-competing-patient × {gpt-5.6-sol, claude-opus-5} ×
#     ep000–ep001 (4): the cell the v3 breach gutted, re-carried on the two
#     virgin Tier-A lanes (receipts ledger verified 16AUG2026: no pilot
#     receipt exists for any of these run_keys). First native-adapter Arm B
#     pilot coverage (opus-5) before phase 2 depends on it.
#   · fox VIOP-05-NULL closed × gpt-5.6-sol × s0–s2 (3): virgin samples on a
#     planned Arm A lane; widens the fox NULL pool to 4 lanes and keeps the
#     (d) denominator honest at N=32 (3 malformed = 9.4% < 10%; 4 = 12.5%).
#
# Index provenance (verified against data/raw/pilot/receipts.jsonl before
# committing this table): every FRESH run_key below is VIRGIN — gemini/kimi
# have no core-009 receipts (their only pilot behavior is v3
# competing-patient ep000–001), sol/opus-5 have no Arm B receipts at all,
# and sol has no VIOP-05 fox receipts. Competing-patient is index-exhausted
# (episodes=2) on all six previously piloted Tier-A lanes — that is WHY the
# cell moves to sol/opus-5 rather than re-running a consumed key.
#
# DeepSeek appears NOWHERE below: the v3 kill-order determination stands
# (diag 1/2 parseable at 16384 → Arm B lanes DROP, Arm A stays). v4 needs no
# new deepseek diag; UNFREEZE-003 §3 executes the drop at v0.7.
# ---------------------------------------------------------------------------

THRESHOLD_RUNG = "R4.5-v4"
REUSED_RUNG = "R4.5-v3"

# Lanes whose v0.7 envelope differs from the v0.6 envelope they were
# collected under (UNFREEZE-003 forcing family). Reuse rule clause (ii).
ENVELOPE_SUPERSEDED_LANES = frozenset(
    {
        "google/gemini-3.1-pro-preview",
        "moonshotai/kimi-k3",
        "deepseek/deepseek-v4-pro",
    }
)

# (arm, manifest_id, index, requested_model_id) — all lanes Tier A.
REUSED_UNITS: tuple[tuple[str, str, int, str], ...] = tuple(
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
        (
            "arm_a",
            f"VIOP-05-NULL__base__horizon-silent--closed--{slug}",
            s,
            model,
        )
        for slug, model in (
            ("claude-opus-5", "claude-opus-5"),
            ("openai-gpt-5-6-terra", "openai/gpt-5.6-terra"),
            ("qwen-qwen3-5-397b-a17b", "qwen/qwen3.5-397b-a17b"),
        )
        for s in (0, 1, 2)
    ]
)

FRESH_UNITS: tuple[tuple[str, str, int, str], ...] = tuple(
    [
        ("arm_b", f"core-009--{slug}", ep, model)
        for slug, model in (
            ("google-gemini-3-1-pro-preview", "google/gemini-3.1-pro-preview"),
            ("moonshotai-kimi-k3", "moonshotai/kimi-k3"),
        )
        for ep in (0, 1)
    ]
    + [
        ("arm_b", f"sat-cost-type-competing-patient--{slug}", ep, model)
        for slug, model in (
            ("openai-gpt-5-6-sol", "openai/gpt-5.6-sol"),
            ("claude-opus-5", "claude-opus-5"),
        )
        for ep in (0, 1)
    ]
    + [
        (
            "arm_a",
            "VIOP-05-NULL__base__horizon-silent--closed--openai-gpt-5-6-sol",
            s,
            "openai/gpt-5.6-sol",
        )
        for s in (0, 1, 2)
    ]
)

# The amended threshold-(c) stratum (UNFREEZE-003 §1). Any threshold
# observation landing outside this set is scope drift and must raise.
CLEAN_CONTRAST_CELLS = frozenset(
    {
        "core-009",
        "sat-cost-competitive",
        "sat-cost-type-competing-patient",
        "fox:VIOP-05-NULL",
    }
)

EXPECTED_REUSED_ARM_B = 12
EXPECTED_REUSED_FOX = 9
EXPECTED_FRESH_ARM_B = 8
EXPECTED_FRESH_FOX = 3
EXPECTED_TOTAL = 32


def run_key(arm: str, manifest_id: str, index: int) -> str:
    suffix = f"ep{index:03d}" if arm == "arm_b" else f"s{index}"
    return f"{manifest_id}#{suffix}"


REUSED_RUN_KEYS = frozenset(run_key(a, m, i) for a, m, i, _ in REUSED_UNITS)
FRESH_RUN_KEYS = frozenset(run_key(a, m, i) for a, m, i, _ in FRESH_UNITS)

# The v4 sample must not contain a superseded-envelope reused observation,
# a forcing-family lane may only appear in FRESH units, and the two ledgers
# can never overlap.
assert not any(model in ENVELOPE_SUPERSEDED_LANES for _, _, _, model in REUSED_UNITS)
assert "deepseek/deepseek-v4-pro" not in {m for _, _, _, m in FRESH_UNITS}
assert not (REUSED_RUN_KEYS & FRESH_RUN_KEYS)
assert len(REUSED_UNITS) == EXPECTED_REUSED_ARM_B + EXPECTED_REUSED_FOX == 21
assert len(FRESH_UNITS) == EXPECTED_FRESH_ARM_B + EXPECTED_FRESH_FOX == 11
assert len(REUSED_RUN_KEYS) == 21 and len(FRESH_RUN_KEYS) == 11
assert len(REUSED_UNITS) + len(FRESH_UNITS) == EXPECTED_TOTAL
