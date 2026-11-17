# AWS setup (new student account, $0 target)

Verified against AWS pages in Nov 2026: new accounts get a **Free plan** for up to 6 months with $100 sign-up credits (+ up to $100 more for onboarding activities). When the 6 months end or the credits run out, a Free-plan account is **closed automatically**. You are not billed unless you upgrade to the Paid plan. Lambda's own free allowance (1M requests, 400,000 GB-s per month) is always free.

## 1. Account
1. Sign up at https://aws.amazon.com/free and choose the **Free plan** (not Paid). AWS will ask for identity/payment verification; check what it asks for at sign-up.
2. Turn on MFA for the root user. Never use root for the CLI.
3. Billing → **Budgets** → create a zero-spend or very small budget alert. Check Billing → Credits for the expiry date.
4. Pick region **ap-south-1 (Mumbai)** and use it everywhere.

## 2. Identities (two IAM users)
- `cloudcost-admin`: used only for the one-time setup scripts (creates a Lambda role and functions). Easiest is AdministratorAccess; delete its keys when finished.
- `cloudcost-app`: used by the dashboard. Attach the policy in `scripts/iam_policy.json`. It can read metrics and change memory only on `cloudcost-demo-*` functions.

Create access keys for each, then on Windows install AWS CLI v2 (MSI from aws.amazon.com/cli) and run:

```powershell
aws configure --profile cloudcost-admin
aws configure --profile cloudcost-app
```
Keys live in `%UserProfile%\.aws\credentials`, never in this project.

## 3. Verify and create the demo workloads
```powershell
$env:AWS_PROFILE="cloudcost-admin"
python scripts\verify_aws.py
python scripts\create_test_functions.py     # light (1024 MB, over-provisioned) + compute (256 MB, CPU-starved)
python scripts\generate_load.py 60          # 60 invocations each (cap 120)
```
Logs are set to 7-day retention. Compute Optimizer needs 50+ invocations in 14 days.

## 4. Compute Optimizer
Console → Compute Optimizer → opt in (once). Results can take up to about a day. If your Free plan blocks it, `verify_aws.py` says so and the app falls back to its labelled heuristic. Do not upgrade just for this.

## 5. Point the dashboard at AWS
```powershell
$env:AWS_PROFILE="cloudcost-app"
$env:CLOUDCOST_MODE="aws"
uvicorn backend.app.main:app --port 8000
```
Dashboard shows **LIVE AWS**. It is read-only until `allow_writes: true` (or `CLOUDCOST_ALLOW_WRITES=true`).

## 6. Clean up when finished
```powershell
$env:AWS_PROFILE="cloudcost-admin"
python scripts\cleanup.py --yes
```
Then deactivate the IAM access keys.
