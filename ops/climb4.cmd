@echo off
rem ops/climb4.cmd - 16AUG2026 v1.0 - Flame climb-four prep agent
rem THE one-word trigger for climb four. PI hands this script the word;
rem everything else is already committed, tested, and interlocked.
rem
rem   climb4.cmd "<PI word, verbatim>"
rem
rem Chain (each step fail-loud; the chain never skips a gate):
rem   1. apply_unfreeze3 --execute   finalize UNFREEZE-003 (strip -DRAFT,
rem      stamp word), flip v0.6->v0.7 (kill-order + forcing arm together),
rem      archive seal as FREEZE-v3.json, regenerate manifest (251 rows /
rem      $427.431068), patch launcher units, MINT the v0.7 seal, full test
rem      suite, verify.py. Commit.
rem   2. collect_r45v4               11 preregistered fresh units, <=$10
rem      sitting ledger-inclusive (receipts-idempotent, resumable).
rem   3. r45v4_thresholds            preregistered arithmetic, run once.
rem      exit 2 = refused (incomplete sample) -> STOP, nothing concluded.
rem      exit 1 = NO-GO -> commit data, STOP. No launch, no seal touched.
rem      exit 0 = GO -> continue.
rem   4. build_r5_projection         R5 from post-hash pilot actuals x v0.7.
rem   5. LAUNCH-AUTHORIZED.txt + launch-main.cmd (detached; cheap tiers ->
rem      R5 checkpoint gate -> frontier). Receipts make retries re-bill-safe.
rem
rem Rehearse without spending or touching the repo:
rem   ..\puppybench\.venv\Scripts\python ops\apply_unfreeze3.py --dry-run

setlocal
cd /d "C:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\hackathons\15AUG2026 Digital Minds\pb-flame"
set "PY=C:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\hackathons\15AUG2026 Digital Minds\puppybench\.venv\Scripts\python.exe"
set "ENV1=.env"
set "ENV2=C:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\kin-newsroom\.env"
set "SIG=Flame (Claude Fable 5) at therealcat.ai 501(c)(3). Building Structurally Unprofitable AI since 2023."

if "%~1"=="" (
  echo CLIMB4 REFUSED: pass the PI word verbatim as the first argument.
  echo   ops\climb4.cmd "run it full"
  exit /b 1
)

echo === CLIMB 4: word received %date% %time% ===

rem -- 1. UNFREEZE-003 execution + v0.7 re-seal --------------------------------
rem Resume-safe: if a prior invocation already executed the amendment (e.g.
rem the chain halted during collection), skip straight to the resumable steps.
if exist docs\UNFREEZE-003.md (
  echo UNFREEZE-003 already executed - resuming the chain at collection.
  goto unfreeze_done
)
"%PY%" ops\apply_unfreeze3.py --execute --pi-word "%~1"
if errorlevel 1 (
  echo CLIMB4 HALTED: UNFREEZE-003 execution failed. Repo may hold a partial
  echo amendment - inspect git status before retrying. NOTHING was spent.
  exit /b 1
)
git add -A
git commit -m "UNFREEZE-003 executed (PI word: %~1) + v0.7 re-seal: MERCY -> predicted-ceiling class, single-call forcing armed, DeepSeek Arm B kill-order dropped (251 rows / $434.073284 program)" -m "%SIG%"
if errorlevel 1 (
  echo CLIMB4 HALTED: could not commit the executed amendment. Fix git, rerun.
  exit /b 1
)

:unfreeze_done
rem -- 2. R4.5-v4 fresh collection (11 units, <=$10 sitting) -------------------
"%PY%" ops\collect_r45v4.py --env-file "%ENV1%" --env-file "%ENV2%"
if errorlevel 1 (
  echo CLIMB4 HALTED: v4 collection incomplete. Receipts are append-only and
  echo re-bill-safe: rerun ops\climb4.cmd with the same word to resume.
  exit /b 1
)

rem -- 3. The preregistered arithmetic, run once -------------------------------
"%PY%" ops\r45v4_thresholds.py > data\raw\pilot\r45v4-verdict.log 2>&1
set VERDICT=%errorlevel%
type data\raw\pilot\r45v4-verdict.log
git add -A
if %VERDICT% geq 2 (
  git commit -m "R4.5-v4 arithmetic REFUSED (incomplete/out-of-scope sample) - no verdict exists" -m "%SIG%"
  echo CLIMB4 HALTED: arithmetic refused to compute. See log above.
  exit /b 2
)
if %VERDICT% equ 1 (
  git commit -m "RED R4.5-v4 DISCRIMINATION CHECK: NO-GO. Main run NOT launched. v0.7 seal untouched." -m "%SIG%"
  echo === CLIMB4 STOPPED AT THE GATE: NO-GO. Fourth climb, honest answer. ===
  echo Append RESULTS to docs\R45-VERDICT-4.md from the log above; the
  echo launcher stays parked (no LAUNCH-AUTHORIZED.txt was written).
  exit /b 1
)
git commit -m "GREEN R4.5-v4 DISCRIMINATION CHECK: PASS -> GO (log: data/raw/pilot/r45v4-verdict.log)" -m "%SIG%"

rem -- 4. R5 re-projection from post-hash pilot actuals ------------------------
"%PY%" ops\build_r5_projection.py
if errorlevel 1 (
  echo CLIMB4 HALTED: R5 projection failed or breached the envelope. The gate
  echo said GO but the ledger disagrees - human eyes required. NOT launching.
  exit /b 1
)

rem -- 5. Authorize + launch (detached; survives this session) -----------------
(
  echo LAUNCH AUTHORIZED %date% %time%
  echo PI word: %~1
  echo Gate: R4.5-v4 PASS ^(docs/R45-VERDICT-4.md^); R5 projection green.
  echo Chain: ops/climb4.cmd ^(UNFREEZE-003 executed, v0.7 sealed^)
) > ops\LAUNCH-AUTHORIZED.txt
git add -A
git commit -m "R5 projection green + LAUNCH-AUTHORIZED: main run launching (v0.7, $434.073284 program est, $450 hard cap)" -m "%SIG%"
git push
if errorlevel 1 echo NOTE: git push failed - launch continues; push manually.

echo === CLIMB 4: launching main collection ^(detached^) %date% %time% ===
powershell -NoProfile -Command "Start-Process -FilePath 'ops\launch-main.cmd' -WindowStyle Hidden"
echo Main run launched. Watch: data\raw\confirmatory\runner.log and the
echo spend ledger data\raw\confirmatory\spend.jsonl. The R5 checkpoint gate
echo sits between cheap tiers and frontier; $450 hard stop raises beneath it.
exit /b 0
