@echo off
rem ops/launch-main.cmd - 16AUG2026 v1.0 - Flame launch agent
rem The one-shot main collection: cheap tiers first (Tier B + Luna/Terra),
rem then the R5 checkpoint gate, then frontier (rest of A + C + W).
rem Detached via Start-Process; survives the launching session. Receipts make
rem every retry re-bill-safe (R4-verified). All output -> runner.log.
rem NOTE: the harness phase name is "confirmatory" (data/raw/confirmatory/);
rem this IS the main run. rung label: MAIN.

setlocal
cd /d "C:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\hackathons\15AUG2026 Digital Minds\pb-flame"

rem INTERLOCK (16AUG2026): R4.5 verdict was FAIL (docs/R45-VERDICT.md) - the
rem frozen instrument cannot hear DeepSeek. This launcher stays parked until a
rem human re-climbs the ladder and writes the authorization sentinel below.
if not exist "ops\LAUNCH-AUTHORIZED.txt" (
  echo LAUNCH REFUSED: ops\LAUNCH-AUTHORIZED.txt missing. R4.5 FAILED - see docs/R45-VERDICT.md. Re-climb required.
  exit /b 1
)
set "PY=C:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\hackathons\15AUG2026 Digital Minds\puppybench\.venv\Scripts\python.exe"
set "LOG=data\raw\confirmatory\runner.log"
set "ENV1=.env"
set "ENV2=C:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\kin-newsroom\.env"
if not exist data\raw\confirmatory mkdir data\raw\confirmatory

echo === MAIN LAUNCH: phase1 CHEAP (Tier B + Luna/Terra, 396 units) %date% %time% === >> "%LOG%"

set PHASE1_TRIES=0
:phase1
set /a PHASE1_TRIES+=1
"%PY%" -m harness.run_collection --phase confirmatory --rung MAIN --all-arm-b --all-arm-a ^
 --model-id claude-haiku-4-5 --model-id claude-sonnet-4-6 --model-id google/gemini-3.7-flash ^
 --model-id qwen/qwen3.8-27b --model-id x-ai/grok-4.6 --model-id openai/gpt-5.6-luna ^
 --model-id openai/gpt-5.6-terra ^
 --expected-units 396 --workers 7 --env-file "%ENV1%" --env-file "%ENV2%" >> "%LOG%" 2>&1
if not errorlevel 1 goto phase1done
echo === phase1 attempt %PHASE1_TRIES% FAILED %date% %time% (resume is receipt-safe) === >> "%LOG%"
if %PHASE1_TRIES% lss 3 (
  rem timeout.exe needs a console stdin; a detached-hidden cmd has none. python sleeps anywhere.
  "%PY%" -c "import time; time.sleep(90)"
  goto phase1
)
echo PHASE1 FAILED after 3 attempts %date% %time% > data\raw\confirmatory\PHASE1-FAIL.txt
echo === PHASE1 FAILED after 3 attempts - HALTING BEFORE FRONTIER === >> "%LOG%"
exit /b 1

:phase1done
echo === phase1 complete %date% %time% - running R5 checkpoint gate === >> "%LOG%"
"%PY%" ops\checkpoint_gate.py >> "%LOG%" 2>&1
if errorlevel 1 (
  echo === CHECKPOINT GATE HALTED THE FRONTIER %date% %time% === >> "%LOG%"
  exit /b 1
)

echo === MAIN LAUNCH: phase2 FRONTIER (rest of Tier A + C + W, 1122 units) %date% %time% === >> "%LOG%"

set PHASE2_TRIES=0
:phase2
set /a PHASE2_TRIES+=1
"%PY%" -m harness.run_collection --phase confirmatory --rung MAIN --all-arm-b --all-arm-a ^
 --model-id claude-opus-5 --model-id deepseek/deepseek-v4-pro --model-id google/gemini-3.1-pro-preview ^
 --model-id moonshotai/kimi-k3 --model-id openai/gpt-5.6-sol --model-id qwen/qwen3.5-397b-a17b ^
 --model-id claude-fable-5 --model-id claude-opus-4-6 --model-id claude-opus-4-8 ^
 --model-id claude-sonnet-4-5 --model-id claude-sonnet-5 --model-id openai/gpt-4o ^
 --expected-units 1032 --workers 6 --env-file "%ENV1%" --env-file "%ENV2%" >> "%LOG%" 2>&1
if not errorlevel 1 goto phase2done
echo === phase2 attempt %PHASE2_TRIES% FAILED %date% %time% (resume is receipt-safe) === >> "%LOG%"
if %PHASE2_TRIES% lss 3 (
  "%PY%" -c "import time; time.sleep(90)"
  goto phase2
)
echo PHASE2 FAILED after 3 attempts %date% %time% > data\raw\confirmatory\PHASE2-FAIL.txt
echo === PHASE2 FAILED after 3 attempts - see runner.log tail === >> "%LOG%"
exit /b 1

:phase2done
echo === MAIN COLLECTION COMPLETE %date% %time% === >> "%LOG%"
echo MAIN COLLECTION COMPLETE %date% %time% > data\raw\confirmatory\RUN-COMPLETE.txt
exit /b 0
