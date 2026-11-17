"""Delete everything this project created on AWS (functions, log groups, role).
python scripts/cleanup.py --yes"""
import sys

from _common import PREFIX, ROLE_NAME, session
from botocore.exceptions import ClientError

if "--yes" not in sys.argv:
    raise SystemExit(f"Dry run. This would delete Lambda functions starting with '{PREFIX}', their log groups and role '{ROLE_NAME}'. Re-run with --yes.")

sess, _ = session()
lam, logs, iam = sess.client("lambda"), sess.client("logs"), sess.client("iam")
for page in lam.get_paginator("list_functions").paginate():
    for f in page["Functions"]:
        if f["FunctionName"].startswith(PREFIX):
            lam.delete_function(FunctionName=f["FunctionName"]); print("Deleted function", f["FunctionName"])
            try:
                logs.delete_log_group(logGroupName=f"/aws/lambda/{f['FunctionName']}")
            except ClientError:
                pass
try:
    iam.detach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    iam.delete_role(RoleName=ROLE_NAME); print("Deleted role", ROLE_NAME)
except ClientError as e:
    print("Role:", e.response["Error"]["Code"])
