# Viva preparation

**What is AWS Lambda?** Serverless compute: you upload code, AWS runs it on demand and bills per request and per GB-second. No servers to manage.

**What does memory do in Lambda?** It sets memory and, proportionally, CPU (about one vCPU at 1,769 MB). More memory can shorten duration, so cost = memory x duration, not memory alone.

**Why can lowering memory fail to save money?** Less memory means less CPU; a CPU-bound function runs longer, cancelling the saving. That is why the app verifies duration and cost after every change and supports rollback.

**What is CloudWatch?** AWS monitoring. Lambda publishes Invocations, Duration, Errors, Throttles and ConcurrentExecutions automatically. Peak memory is not a standard metric; it is in the `REPORT` log line (`Max Memory Used`).

**What is Compute Optimizer?** ML-based right-sizing service. For Lambda it needs 50+ invocations in the last 14 days and memory of 1,792 MB or less; otherwise the finding is Unavailable. Findings: Optimized, NotOptimized, Unavailable.

**Why GetMetricStatistics, not GetMetricData?** The former is inside CloudWatch's free API allowance; GetMetricData is always charged.

**IaaS vs PaaS vs SaaS with examples?** EC2 (IaaS), Lambda/Elastic Beanstalk (PaaS/FaaS), WorkMail/Chime (SaaS).

**Why IAM least privilege?** The app's identity can only read metrics and change `cloudcost-demo-*` functions, limiting damage from a bug or leaked key.

**Why a backend instead of calling AWS from React?** Browser code is public; credentials must stay server-side.

**How is cost kept at $0?** Free plan, local dashboard/database, tiny bounded workloads, free-tier-safe APIs, log retention, cleanup script, budget alert.

**What happens when the Free plan ends?** Up to 6 months or when credits run out, whichever first; the account closes unless upgraded.

**How do you avoid showing fake savings?** Three labels: AWS figure, Estimate, Demo. Unavailable recommendations show no number.

**What if Compute Optimizer is unavailable?** A heuristic (peak memory x 1.3 headroom) is used and labelled as not from AWS.

**Safety of changes?** Dry-run default, approval, drift check, backup, managed-prefix scope, 75% single-step limit, verification, rollback, audit trail.

**Scalability?** Pagination for inventory; cap of 50 analysed functions; cached metrics; could move storage to S3/DynamoDB and run on Lambda later.
