# Patient endpoints (apparatus, price $0)

| Role | Endpoint | Model | Notes |
|---|---|---|---|
| ModelPatient primary | http://localhost:11434/v1 | qwen2.5:0.5b | ollama, Windows box, verified 15AUG2026 ~15:30 ET |
| ModelPatient fallback | SubprocessPatient | (real child process) | wiring-gate verified, no network |
| Big sibling (subject, NOT patient) | http://192.168.1.103:8000/v1 | qwen35-397b | Spark cluster — do not use as patient |
