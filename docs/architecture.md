# Architecture

```
React (localhost:5173)  ->  FastAPI (127.0.0.1:8000)  ->  Provider  ->  AWS (Lambda, CloudWatch, Compute Optimizer, STS)
                                   |                          \-> DemoProvider (sample data)
                                   +-> engine/ (pure logic)   
                                   +-> data/ , reports/ (local JSON/CSV)
```

- **Provider** (`backend/app/aws/provider.py`): the only place boto3 is used. `LiveProvider` wraps three gateways (Lambda, CloudWatch, Optimizer) on one shared session; `DemoProvider` fakes the same interface.
- **Services** orchestrate: inventory, metrics (cached), recommendations (+ fallback), optimization workflow, reports.
- **Engine** has no AWS code: cost model, safety rules, analysis, approval state machine, backup, rollback, before/after comparison. This is why tests need no AWS.
- **State machine**: previewed -> approved -> applied -> rolled_back; previewed -> rejected; approved -> failed/rejected. Illegal transitions are refused.

## Apply safeguards
approved only -> writes enabled (live mode) -> drift check (memory still equals preview) -> rules re-validated -> backup saved -> update + wait for `LastUpdateStatus=Successful` -> audit record. A failed update is recorded as `failed`; memory is untouched.

## Data
`data/inventory|metrics|recommendations|backups|history` JSON with account/region/timestamps, git-ignored. `history/optimizations.json` is the audit trail.
