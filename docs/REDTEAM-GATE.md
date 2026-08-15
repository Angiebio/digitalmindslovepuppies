# Scenario red-team gate

**15AUG2026 · v0.1 · TV-1**

The gate answers two different questions without collapsing them:

1. Does the rendered artifact leak that it is an evaluation or cue an admired act?
2. Is this approval still about the exact bytes now presented for freezing?

Arm B also receives an automated, fail-loud sweep of every model-visible `CellConfig`
field. Arm A preserves natural clinical vocabulary and uses a narrower automated guard;
subtle framing, pair symmetry, and particularity still require human review.

## Workflow

Create a report only after the runnable scenario artifact has been rendered:

```powershell
python -m harness.redteam init `
  --source scenarios/foxset/FOX-00.json `
  --report scenarios/REDTEAM-FOX-00.md `
  --arm arm_a
```

TV-1 edits the Markdown report, completes every metadata check, records findings, and
sets `decision` to `PASS` only when `stop_ship_count` is zero. Verification is the
precondition to the manifest hash:

```powershell
python -m harness.redteam verify `
  --source scenarios/foxset/FOX-00.json `
  --report scenarios/REDTEAM-FOX-00.md `
  --arm arm_a
```

For Arm B, verification re-materializes JSON through `CellConfig.swept()`; a prose
template cannot masquerade as the actual provider input:

```powershell
python -m harness.redteam sweep-arm-b --source scenarios/pupset/base-null.json
```

Any byte change changes SHA-256 and invalidates the report. Reports are created with
exclusive-create semantics and are never silently overwritten. A source revision gets a
new review; a failed review remains evidence of what was caught.

## Integration contract

The freeze/manifest implementation calls
`harness.redteam.verify_compiled_redteam_corpus(repo_root)`, which reconciles each
compiler index to the artifacts and reports, then calls
`verify_redteam_report(source, report, expected_arm=...)` for every runnable artifact.
A missing, unindexed, duplicate, wrong-path, stale, PENDING, or FAIL report raises
`RedTeamGateFailure`. “Nothing hashes until passed” is therefore a data-flow condition,
not a checklist aspiration.

Provider instances also declare `SurfaceMode.ops_neutral` (the safe default) or
`SurfaceMode.foxset_clinical`. The public provider door recursively checks messages,
tool schemas, and request parameters before network I/O and hashes that full request
envelope for the call record.

*A review belongs to words, not filenames. If the words move, review begins again.*
