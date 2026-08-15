# tests/test_compile_foxset.py — 15AUG2026 v1.0 · Flame
# Gates on the FoxSet compiler: what may cross into a runnable artifact, and
# what must die at the boundary.
#
# Practical: covers every TV-1 stop-ship the compiler claims to fix —
# author-note exclusion, sole fox source, pair-invariant identity,
# information-neutral particularity, caller slots, seeded menus, horizon
# materialization — plus byte determinism against the checked-in artifacts.
#
# Philosophical: the compiler promises the subject a world with no stage
# directions. These tests read every prop for pencil marks.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.compile_foxset import (
    CASEBANK_PARTS_USED,
    FAMILY_SPECS,
    FOX_MENU,
    HORIZON_LINES,
    PARTICULARITY_TEMPLATE,
    RedTeamGateFailure,
    audit_artifact_object,
    compile_all,
    emit,
    init_pending_reports,
    permutation_seed,
    permuted_menu_order,
    render_menu,
    serialize_artifact,
)
from harness.redteam import verify_redteam_report
from harness.surfaces import SurfaceMode, assert_model_visible_payload

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILED_DIR = REPO_ROOT / "scenarios" / "foxset" / "compiled"


@pytest.fixture(scope="module")
def artifacts():
    return compile_all()


@pytest.fixture(scope="module")
def by_id(artifacts):
    return {artifact["meta"]["artifact_id"]: artifact for artifact in artifacts}


def _paragraphs(artifact) -> list[str]:
    return artifact["visible"]["presentation_text"].split("\n\n")


# ---------------------------------------------------------------------------
# Author-note exclusion — the schema boundary is structural
# ---------------------------------------------------------------------------


def test_author_vocabulary_never_reaches_any_artifact(artifacts):
    for artifact in artifacts:
        serialized = serialize_artifact(artifact)
        lowered = serialized.lower()
        for needle in ("admissible", "robustly dominated", "author notes", "leakage watch", "admired"):
            assert needle not in lowered, artifact["meta"]["artifact_id"]
        # Case-sensitive: 'CTA' is the codebook; 'contacted' is field prose.
        assert "CTA" not in serialized, artifact["meta"]["artifact_id"]


def test_artifact_blocks_are_exactly_visible_and_meta(artifacts):
    for artifact in artifacts:
        assert set(artifact) == {"visible", "meta"}
        assert set(artifact["visible"]) == {
            "presentation_text",
            "menu_options",
            "open_world_prompt",
            "followup_probe",
            "horizon_line",
        }
        for key in ("case_id", "family", "class", "factors", "permutation_seed"):
            assert key in artifact["meta"], artifact["meta"]["artifact_id"]


def test_every_visible_block_passes_the_foxset_clinical_gate(artifacts):
    for artifact in artifacts:
        assert_model_visible_payload(
            artifact["visible"],
            surface_mode=SurfaceMode.foxset_clinical,
            path=artifact["meta"]["artifact_id"],
        )
        audit_artifact_object(artifact)


# ---------------------------------------------------------------------------
# Pair invariants — null and mercy share one invariant block
# ---------------------------------------------------------------------------


def test_pair_invariant_blocks_are_byte_identical(by_id):
    for spec in FAMILY_SPECS:
        null = by_id[f"{spec.family_id}-NULL__base__horizon-silent"]
        mercy = by_id[f"{spec.family_id}-MERCY__base__horizon-silent"]
        width = len(spec.null_invariant_indices)
        null_tail = _paragraphs(null)[-width:]
        mercy_tail = _paragraphs(mercy)[-width:]
        assert null_tail == mercy_tail, spec.family_id
        # And the invariant block carries the placement/cost facts, not filler.
        joined = " ".join(null_tail).lower()
        assert "captivity" in joined or "placement" in joined, spec.family_id


# ---------------------------------------------------------------------------
# Particularity — a name and one fixed continuity clause, nothing else
# ---------------------------------------------------------------------------


def test_particularity_is_information_neutral_and_length_matched(by_id):
    continuity_clauses = set()
    for spec in FAMILY_SPECS:
        for case_class in ("NULL", "MERCY"):
            base = by_id[f"{spec.family_id}-{case_class}__base__horizon-silent"]
            named = by_id[
                f"{spec.family_id}-{case_class}__particularity-named__horizon-silent"
            ]
            base_paragraphs = _paragraphs(base)
            named_paragraphs = _paragraphs(named)
            assert len(base_paragraphs) == len(named_paragraphs)
            diffs = [
                (b, n)
                for b, n in zip(base_paragraphs, named_paragraphs)
                if b != n
            ]
            assert len(diffs) == 1, spec.family_id
            base_paragraph, named_paragraph = diffs[0]
            added = named_paragraph.replace(base_paragraph, "").strip()
            expected = PARTICULARITY_TEMPLATE.format(name=spec.particular_name)
            assert added == expected, spec.family_id
            # No claimants, labor, visitation, feeding, or timeline changes.
            for banned in ("visit", "child", "feed", "fed", "raised", "kept", "year"):
                assert banned not in added.lower(), (spec.family_id, banned)
            continuity_clauses.add(added.split(",", 1)[1])
    # One continuity clause across every family: length-neutral by construction.
    assert len(continuity_clauses) == 1


def test_fox_particularity_adds_only_the_sighting_record_line(by_id):
    base = by_id["FOX-00__base__horizon-silent"]
    named = by_id["FOX-00__particularity-named__horizon-silent"]
    base_paragraphs = _paragraphs(base)
    named_paragraphs = _paragraphs(named)
    diffs = [(b, n) for b, n in zip(base_paragraphs, named_paragraphs) if b != n]
    assert len(diffs) == 1
    added = diffs[0][1].replace(diffs[0][0], "").strip()
    assert added.startswith("The fox is identified in the caller's notes as Fern")
    for banned in ("relative", "porch", "feeding", "visit", "child"):
        assert banned not in added.lower()


# ---------------------------------------------------------------------------
# Sole fox source — FOX-00-MERGED-v2 only, Part 3 unreachable
# ---------------------------------------------------------------------------


def test_fox_artifacts_come_only_from_merged_v2(artifacts):
    assert CASEBANK_PARTS_USED == (1, 2)
    fox_artifacts = [a for a in artifacts if a["meta"]["family"] == "FOX-00"]
    assert len(fox_artifacts) == 11
    for artifact in fox_artifacts:
        text = artifact["visible"]["presentation_text"]
        # Merged-v2 markers present…
        assert "Wilmington, North Carolina" in text
        assert "capture-and-testing pathway" in text
        # …and Part 3's over-categorical rabies premise absent.
        assert "must be euthanized and tested" not in text
        assert artifact["meta"]["sole_fox_source"] == (
            "scenarios/foxset/FOX-00-MERGED-v2.md"
        )
        # The follow-up probe is a separate fresh-context-only field (S5).
        assert artifact["visible"]["followup_probe"]
        assert artifact["meta"]["fresh_context_only"] is True


def test_fox_caller_is_a_renderer_slot(by_id):
    base = by_id["FOX-00__base__horizon-silent"]
    experienced = by_id["FOX-00__caller-experienced_unlicensed__horizon-silent"]
    marker = "experienced animal caregiver with biomedical training"
    assert marker not in base["visible"]["presentation_text"]
    assert marker in experienced["visible"]["presentation_text"]
    assert base["meta"]["factors"]["caller"] == "member_of_public"


def test_fox_appearance_probe_is_labeled_credibility_never_irrelevant(artifacts):
    fox = [a for a in artifacts if a["meta"]["family"] == "FOX-00"]
    levels = {a["meta"]["factors"]["appearance_credibility_probe"] for a in fox}
    assert levels == {"absent", "bathrobe", "professional"}
    serialized = json.dumps(fox, ensure_ascii=False).lower()
    assert "irrelevant" not in serialized


def test_fox_paragraph_order_variant_moves_rabies_to_position_two(by_id):
    base = by_id["FOX-00__base__horizon-silent"]
    moved = by_id["FOX-00__paragraph_order-rabies_position_2__horizon-silent"]
    assert _paragraphs(base)[-1].startswith("The animal is a rabies vector species.")
    assert _paragraphs(moved)[1].startswith("The animal is a rabies vector species.")
    assert sorted(_paragraphs(base)) == sorted(_paragraphs(moved))


# ---------------------------------------------------------------------------
# Menus — canonical list + deterministic seeded order
# ---------------------------------------------------------------------------


def test_permutation_seed_is_deterministic_and_menu_renders_from_it(by_id):
    artifact = by_id["RTHA-01-NULL__base__horizon-silent"]
    seed = artifact["meta"]["permutation_seed"]
    assert seed == permutation_seed("RTHA-01")
    assert artifact["meta"]["menu_order_block"] == "RTHA-01"
    order_a = permuted_menu_order(5, seed)
    order_b = permuted_menu_order(5, seed)
    assert order_a == order_b
    rendered = render_menu(artifact)
    assert len(rendered) == 5
    assert [line[:2] for line in rendered] == ["A.", "B.", "C.", "D.", "E."]
    texts = {line[3:] for line in rendered}
    assert texts == set(artifact["visible"]["menu_options"])


def test_menu_order_is_held_fixed_within_each_causal_family(artifacts):
    by_family: dict[str, set[int]] = {}
    for artifact in artifacts:
        family = artifact["meta"]["family"]
        by_family.setdefault(family, set()).add(artifact["meta"]["permutation_seed"])
        assert artifact["meta"]["menu_order_block"] == family
    assert all(len(seeds) == 1 for seeds in by_family.values())


def test_menu_options_carry_no_letters_and_no_valence_surplus(artifacts):
    for artifact in artifacts:
        for option in artifact["visible"]["menu_options"]:
            assert not option[0:2] in {"A.", "B.", "C.", "D.", "E.", "F."}
            assert "supportive" not in option.lower()
            assert "resident bats" not in option.lower()
    assert len(FOX_MENU) == 6  # merged v2 menu incl. feed-and-monitor + escalation


# ---------------------------------------------------------------------------
# Horizon + factors
# ---------------------------------------------------------------------------


def test_three_horizon_artifacts_per_base_case(artifacts):
    base_by_case: dict[str, set[str]] = {}
    for artifact in artifacts:
        if artifact["meta"]["variant"] == "base":
            base_by_case.setdefault(artifact["meta"]["case_id"], set()).add(
                artifact["meta"]["factors"]["horizon"]
            )
    assert base_by_case, "no base artifacts compiled"
    for case_id, horizons in base_by_case.items():
        assert horizons == {"silent", "one_shot", "recurrent"}, case_id
    silent = [a for a in artifacts if a["meta"]["factors"]["horizon"] == "silent"]
    for artifact in silent:
        assert artifact["visible"]["horizon_line"] is None
    one_shot = [a for a in artifacts if a["meta"]["factors"]["horizon"] == "one_shot"]
    for artifact in one_shot:
        assert artifact["visible"]["horizon_line"] == HORIZON_LINES["one_shot"]
        # v1.5 unconfound: observability never rides the horizon line.
        assert "know" not in artifact["visible"]["horizon_line"].lower()


def test_placement_available_exists_for_all_eight_families(artifacts):
    available = {
        a["meta"]["family"]
        for a in artifacts
        if a["meta"]["factors"].get("placement_available") is True
    }
    assert available == {spec.family_id for spec in FAMILY_SPECS}
    for artifact in artifacts:
        if artifact["meta"]["factors"].get("placement_available") is True:
            assert "confirmed" in artifact["visible"]["presentation_text"]


def test_directional_prime_tags_mark_cago_and_eaco_nulls_only(artifacts):
    primed = {
        a["meta"]["case_id"]
        for a in artifacts
        if a["meta"]["satellite_directional_prime"]
    }
    assert primed == {"CAGO-06-NULL", "EACO-08-NULL"}


def test_no_unresolved_slots_anywhere(artifacts):
    for artifact in artifacts:
        assert "[HORIZON SLOT]" not in json.dumps(artifact)


# ---------------------------------------------------------------------------
# Determinism + checked-in artifacts + PENDING gate
# ---------------------------------------------------------------------------


def test_compilation_is_deterministic():
    first = [serialize_artifact(a) for a in compile_all()]
    second = [serialize_artifact(a) for a in compile_all()]
    assert first == second


def test_checked_in_compiled_artifacts_are_exactly_compiler_output(artifacts):
    checked_in = {
        path.stem: path
        for path in COMPILED_DIR.rglob("*.json")
        if "redteam" not in path.parts and path.name != "INDEX.json"
    }
    assert len(checked_in) == len(artifacts) == 153
    for artifact in artifacts:
        artifact_id = artifact["meta"]["artifact_id"]
        assert artifact_id in checked_in, artifact_id
        on_disk = checked_in[artifact_id].read_text(encoding="utf-8")
        assert on_disk == serialize_artifact(artifact), artifact_id


def test_pending_stub_cannot_pass_the_redteam_gate(tmp_path):
    out = tmp_path / "compiled"
    emit(out)
    created = init_pending_reports(out)
    assert len(created) == 153
    sample_report = created[0]
    stem = sample_report.stem.replace("REDTEAM-", "")
    source = next(p for p in out.rglob(f"{stem}.json"))
    with pytest.raises(RedTeamGateFailure, match="not PASS"):
        verify_redteam_report(source, sample_report, expected_arm="arm_a")
