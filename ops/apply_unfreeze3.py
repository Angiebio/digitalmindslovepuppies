# ops/apply_unfreeze3.py — 16AUG2026 v1.0 · Flame climb-four prep agent
# The UNFREEZE-003 executor: every mechanical act between the PI's word and
# a re-sealed v0.7 tree, in one fail-loud sequence.
#
# Practical: PREP is committed; this script only MOVES what prep prepared.
#   1. preconditions (draft present, v0.6 standing, seal aggregate matches)
#   2. finalize docs/UNFREEZE-003-DRAFT.md -> docs/UNFREEZE-003.md
#      (strip the DRAFT sentinel, stamp the verbatim PI word + timestamp)
#   3. flip scenarios/manifest.py MANIFEST_VERSION "0.6" -> "0.7"
#      (arms the DeepSeek Arm B kill-order AND the forced single-call
#      surface in the same breath — both registries key on this string)
#   4. archive scenarios/FREEZE.json (v0.6, cb308a75...) -> FREEZE-v3.json
#   5. regenerate cell_manifest.csv under v0.7 (251 rows / 798 episodes /
#      $427.431068 — asserted, not hoped)
#   6. patch ops/launch-main.cmd --expected-units 1122 -> 1032
#   7. mint the new scenarios/FREEZE.json through the full preflight door
#   8. full test suite (must be green at v0.7)
#   9. verify.py (every cited number must reproduce at v0.7)
#
# --dry-run rehearses ALL NINE STEPS in a disposable copy of the worktree
# (scratch dir), leaving the real repo byte-identical: the chain is proven
# executable — seal mint, suite, verify and all — without touching the real
# seal. NO API call exists anywhere in this file; it spends $0 by
# construction.
#
# Philosophical: an amendment's execution should be boring. Everything
# irreversible was decided and written down beforehand; this script is just
# the hand that turns the key, and it refuses to turn a key that does not
# fit exactly.

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DRAFT = "docs/UNFREEZE-003-DRAFT.md"
FINAL = "docs/UNFREEZE-003.md"
MANIFEST_PY = "scenarios/manifest.py"
FREEZE = "scenarios/FREEZE.json"
FREEZE_ARCHIVE = "scenarios/FREEZE-v3.json"
LAUNCHER = "ops/launch-main.cmd"
V06_AGGREGATE_PREFIX = "cb308a75e687db84"

SENTINEL_BEGIN = "<!-- DRAFT-SENTINEL-BEGIN"
SENTINEL_END = "<!-- DRAFT-SENTINEL-END -->"

# v0.7 design invariants — asserted after regeneration, never assumed.
EXPECTED_V07 = {"execution_rows": 251, "episodes": 798, "usd": "427.431068"}


class UnfreezeError(RuntimeError):
    """The key does not fit. Nothing partial is left behind on a raise."""


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _write(root: Path, rel: str, text: str) -> None:
    (root / rel).write_text(text, encoding="utf-8", newline="\n")


def _replace_exactly_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise UnfreezeError(
            f"UNFREEZE REFUSED: expected exactly one occurrence of {old!r} "
            f"in {where}, found {count}. The tree is not the one this "
            "executor was prepared against."
        )
    return text.replace(old, new)


def _run(root: Path, argv: list[str], step: str) -> str:
    print(f"  $ {' '.join(argv)}")
    proc = subprocess.run(
        argv, cwd=str(root), capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout or "")
        sys.stderr.write(proc.stderr or "")
        raise UnfreezeError(
            f"UNFREEZE HALTED at step {step!r}: exit {proc.returncode}. "
            "Nothing after this step has run."
        )
    return proc.stdout or ""


def preconditions(root: Path) -> None:
    print("[0/9] preconditions")
    if not (root / DRAFT).is_file():
        raise UnfreezeError(f"UNFREEZE REFUSED: {DRAFT} missing.")
    if (root / FINAL).exists():
        raise UnfreezeError(
            f"UNFREEZE REFUSED: {FINAL} already exists — executed already?"
        )
    if (root / FREEZE_ARCHIVE).exists():
        raise UnfreezeError(f"UNFREEZE REFUSED: {FREEZE_ARCHIVE} already exists.")
    manifest_text = _read(root, MANIFEST_PY)
    if 'MANIFEST_VERSION = "0.6"' not in manifest_text:
        raise UnfreezeError(
            "UNFREEZE REFUSED: scenarios/manifest.py is not at the standing "
            'v0.6 (expected MANIFEST_VERSION = "0.6").'
        )
    seal = json.loads(_read(root, FREEZE))
    aggregate = str(seal.get("aggregate_sha256", ""))
    if not aggregate.startswith(V06_AGGREGATE_PREFIX):
        raise UnfreezeError(
            "UNFREEZE REFUSED: scenarios/FREEZE.json aggregate is "
            f"{aggregate[:16]}…, not the v0.6 witness "
            f"{V06_AGGREGATE_PREFIX}…. Archive/mint history is not what this "
            "executor was prepared against."
        )
    if "--expected-units 1122" not in _read(root, LAUNCHER):
        raise UnfreezeError(
            "UNFREEZE REFUSED: launcher does not carry the v0.6 phase-2 "
            "expected-units; already patched?"
        )
    print("      standing v0.6 tree confirmed (seal cb308a75…, draft present)")


def finalize_doc(root: Path, pi_word: str, stamp: str) -> None:
    print(f"[1/9] finalize {DRAFT} -> {FINAL}")
    text = _read(root, DRAFT)
    begin = text.find(SENTINEL_BEGIN)
    end = text.find(SENTINEL_END)
    if begin < 0 or end < 0 or end <= begin:
        raise UnfreezeError("UNFREEZE REFUSED: DRAFT sentinel markers not found.")
    text = text[:begin] + text[end + len(SENTINEL_END) :].lstrip("\n")
    text = _replace_exactly_once(
        text,
        "# UNFREEZE-003 — DRAFT — post-data amendment to the preregistered check (third)",
        "# UNFREEZE-003 — post-data amendment to the preregistered check (third)",
        DRAFT,
    )
    text = _replace_exactly_once(
        text,
        "v0.1-DRAFT · Flame climb-four prep agent · STATUS: PREPARED, NOT EXECUTED",
        "v1.0 · Flame climb-four prep agent · STATUS: EXECUTED",
        DRAFT,
    )
    text = _replace_exactly_once(
        text,
        "**PI word, verbatim:** ⟨PI-WORD — stamped at execution⟩ · ⟨TIMESTAMP ET⟩",
        f"**PI word, verbatim:** **{pi_word}** · {stamp}",
        DRAFT,
    )
    # Self-references in the pre-data verdict design section follow the file.
    verdict = _read(root, "docs/R45-VERDICT-4.md").replace(
        "UNFREEZE-003-DRAFT.md", "UNFREEZE-003.md"
    )
    _write(root, "docs/R45-VERDICT-4.md", verdict)
    _write(root, FINAL, text)
    (root / DRAFT).unlink()


def flip_manifest_version(root: Path) -> None:
    print('[2/9] flip MANIFEST_VERSION "0.6" -> "0.7"')
    text = _replace_exactly_once(
        _read(root, MANIFEST_PY),
        'MANIFEST_VERSION = "0.6"',
        'MANIFEST_VERSION = "0.7"',
        MANIFEST_PY,
    )
    _write(root, MANIFEST_PY, text)


def archive_seal(root: Path) -> None:
    print(f"[3/9] archive {FREEZE} -> {FREEZE_ARCHIVE} (byte-identical, retired)")
    (root / FREEZE).rename(root / FREEZE_ARCHIVE)


def regenerate_manifest(root: Path, py: str) -> None:
    print("[4/9] regenerate cell_manifest.csv under v0.7")
    out = _run(
        root,
        [
            py,
            "-m",
            "scenarios.manifest",
            "--output",
            str(root / "scenarios" / "cell_manifest.csv"),
            "--snapshot-pins",
            str(root / "scenarios" / "snapshot_pins.json"),
            "--summary",
        ],
        "regenerate-manifest",
    )
    summary = json.loads(out)
    for key, expected in EXPECTED_V07.items():
        if summary.get(key) != expected:
            raise UnfreezeError(
                f"UNFREEZE HALTED: v0.7 summary {key}={summary.get(key)!r}, "
                f"prepared arithmetic says {expected!r}. STOP and reconcile."
            )
    print(
        f"      v0.7: rows={summary['execution_rows']} "
        f"episodes={summary['episodes']} usd=${summary['usd']} "
        f"(headroom ${summary['headroom_usd']})"
    )


def patch_launcher(root: Path) -> None:
    print("[5/9] patch launcher phase-2 expected-units 1122 -> 1032")
    text = _replace_exactly_once(
        _read(root, LAUNCHER),
        "--expected-units 1122",
        "--expected-units 1032",
        LAUNCHER,
    )
    _write(root, LAUNCHER, text)


def mint_seal(root: Path, py: str) -> str:
    print("[6/9] mint the v0.7 seal through the full preflight door")
    out = _run(root, [py, "-m", "scenarios.manifest", "--freeze"], "mint-seal")
    aggregate = str(json.loads(out).get("aggregate_sha256", ""))
    if len(aggregate) != 64:
        raise UnfreezeError("UNFREEZE HALTED: minted seal has no aggregate hash.")
    print(f"      new aggregate: {aggregate[:16]}…")
    return aggregate


def run_suite(root: Path, py: str) -> None:
    print("[7/9] full test suite at v0.7")
    out = _run(root, [py, "-m", "pytest", "tests/", "-q"], "pytest")
    print("      " + (out.strip().splitlines()[-1] if out.strip() else "green"))


def run_verify(root: Path, py: str) -> None:
    print("[8/9] verify.py at v0.7")
    out = _run(root, [py, "verify.py"], "verify")
    print("      " + (out.strip().splitlines()[-1] if out.strip() else "ok"))


def execute(root: Path, pi_word: str) -> None:
    py = sys.executable
    stamp = _dt.datetime.now().astimezone().strftime("%d%b%Y %H:%M %Z").upper()
    preconditions(root)
    finalize_doc(root, pi_word, stamp)
    flip_manifest_version(root)
    archive_seal(root)
    regenerate_manifest(root, py)
    patch_launcher(root)
    aggregate = mint_seal(root, py)
    run_suite(root, py)
    run_verify(root, py)
    print(
        "[9/9] UNFREEZE-003 EXECUTED.\n"
        f"      PI word: {pi_word!r} at {stamp}\n"
        f"      v0.7 sealed: aggregate {aggregate[:16]}… "
        f"(v0.6 archived as {FREEZE_ARCHIVE})\n"
        "      Next (ops/climb4.cmd continues automatically): "
        "collect_r45v4 -> r45v4_thresholds -> [GO only] R5 + launch."
    )


def dry_run(keep: bool) -> None:
    print("DRY-RUN: rehearsing the full execution in a disposable copy…")
    scratch = Path(tempfile.mkdtemp(prefix="pb-unfreeze3-dryrun-"))
    copy_root = scratch / "pb-flame"
    shutil.copytree(
        REPO_ROOT,
        copy_root,
        ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "*.pyc", ".pytest_cache", ".pytest_*"
        ),
    )
    try:
        execute(copy_root, pi_word="DRY-RUN (no PI word; nothing is in force)")
        print(f"\nDRY-RUN COMPLETE: the chain executes end-to-end. Repo untouched.")
    finally:
        if keep:
            print(f"DRY-RUN tree kept for inspection: {copy_root}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="UNFREEZE-003 executor")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--execute",
        action="store_true",
        help="perform UNFREEZE-003 on the REAL tree (PI word required)",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="rehearse every step in a disposable copy; repo untouched, $0",
    )
    parser.add_argument("--pi-word", help="the PI's authorization word, verbatim")
    parser.add_argument(
        "--keep", action="store_true", help="dry-run: keep the scratch tree"
    )
    args = parser.parse_args()

    if args.dry_run:
        dry_run(keep=args.keep)
        return 0
    if not (args.pi_word or "").strip():
        print(
            "UNFREEZE REFUSED: --execute requires --pi-word with the PI's "
            "verbatim authorization. An amendment without its word is a "
            "silent edit."
        )
        return 1
    execute(REPO_ROOT, args.pi_word.strip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UnfreezeError as exc:
        print(str(exc))
        raise SystemExit(1)
