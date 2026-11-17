# Application API (FastAPI, not AWS API Gateway)

Base: `http://127.0.0.1:8000/api` · interactive docs: `/docs`

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/aws/connection` | account, ARN, region, mode, last success |
| GET/PUT | `/settings` | region, analysis days, savings threshold |
| GET | `/lambda/functions` | all functions (paginated in AWS) |
| GET | `/lambda/{name}` | config + metrics + analysis |
| GET | `/metrics/{name}?days=&refresh=` | CloudWatch snapshot (+ peak memory from REPORT logs) |
| GET | `/recommendations?refresh=` | analysis per function + Compute Optimizer status |
| GET | `/cost-analysis` | current vs recommended cost, annualised |
| POST | `/optimization/dry-run` | preview, creates a `previewed` record |
| POST | `/optimization/approve` / `reject` | decision on a record |
| POST | `/optimization/apply` | apply an approved record |
| POST | `/optimization/verify` | before/after comparison |
| POST | `/optimization/rollback` | restore backed-up memory |
| GET | `/optimization/history` | audit records |
| GET | `/reports` · POST `/reports/generate` · GET `/reports/{name}` | list, build, download |

Errors: `{"detail": "...", "notes": [...]}` with 403 (writes disabled), 404, 409 (bad state / drift), 422 (blocked by rules), 502 (AWS problem).
