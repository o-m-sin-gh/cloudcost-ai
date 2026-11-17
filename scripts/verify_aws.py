"""Check that your AWS CLI profile works and what this account can use.  python scripts/verify_aws.py"""
from _common import session
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

try:
    sess, s = session()
    who = sess.client("sts").get_caller_identity()
except (NoCredentialsError, ProfileNotFound) as e:
    raise SystemExit(f"FAIL  No usable credentials ({e}). Run `aws configure` and set AWS_PROFILE.")
print(f"OK    Account {who['Account']}  identity {who['Arn']}  region {s.region}")
if who["Arn"].endswith(":root"):
    print("WARN  You are using the ROOT user. Create an IAM user/role and use that instead.")

try:
    n = len(sess.client("lambda").list_functions()["Functions"])
    print(f"OK    Lambda reachable ({n} function(s) on first page)")
except ClientError as e:
    print("FAIL  Lambda:", e.response["Error"]["Code"])

try:
    st = sess.client("compute-optimizer").get_enrollment_status()["status"]
    print(f"OK    Compute Optimizer enrollment: {st}" + ("" if st == "Active" else "  (opt in via the console, then wait for analysis)"))
except ClientError as e:
    print("INFO  Compute Optimizer unavailable:", e.response["Error"]["Code"],
          "-> CloudCost AI will use its labelled fallback analysis.")

print("\nReminder: check Billing > Free Tier / Credits and create a Budget alert before continuing.")
