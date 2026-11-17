# Cost management

| Rule | How it is enforced |
|---|---|
| No EC2 / RDS / NAT / API Gateway | Not used anywhere; dashboard and API run locally |
| No paid APIs | CloudWatch `GetMetricStatistics` (inside the free 1M API requests) instead of `GetMetricData` (always billed); Cost Explorer API not used |
| Bounded CloudWatch usage | 5 metric calls per function, cached 10 min in `data/metrics`; analysis capped at 50 functions |
| Bounded Lambda usage | `generate_load.py` caps at 120 invocations per function |
| No unbounded logs | demo log groups get 7-day retention |
| Only demo functions modified | `managed_prefix`, plus IAM policy scoped to `cloudcost-demo-*` |
| Cleanup | `scripts/cleanup.py --yes` |

## Cost model
`cost = GB x seconds x invocations x price_per_GB-s + invocations x price_per_request`, using list prices (x86 $0.0000166667, arm64 $0.0000133334 per GB-s, $0.20 per 1M requests), before the free allowance. All values are estimates unless tagged "AWS figure" (from Compute Optimizer).

At demo scale the savings are fractions of a cent per month. The dashboard shows a clearly labelled "at 1M invocations" projection so the effect is visible; it is never presented as real savings.

## Checklist before each session
Check Free plan/credits and expiry, budget alert exists, region is ap-south-1, you are not on the root user.
