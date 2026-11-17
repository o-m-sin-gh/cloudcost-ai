"""Create the two demo Lambda functions (+ role, 7-day log retention).  python scripts/create_test_functions.py"""
import io
import json
import time
import zipfile

from _common import FUNCTIONS, ROLE_NAME, session
from botocore.exceptions import ClientError

LIGHT = '''
import json
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"sum": sum(range(1000))})}
'''
COMPUTE = '''
import hashlib, json
def handler(event, context):
    h = b"cloudcost"
    for _ in range(int(event.get("rounds", 250000))):
        h = hashlib.sha256(h).digest()
    return {"statusCode": 200, "body": json.dumps({"digest": h.hex()[:16]})}
'''


def zip_code(src: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("app.py", src)
    return buf.getvalue()


sess, s = session()
iam, lam, logs = sess.client("iam"), sess.client("lambda"), sess.client("logs")

trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
try:
    role = iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust), Tags=[{"Key": "Project", "Value": "cloudcost-ai"}])["Role"]
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    print("Created role", ROLE_NAME, "- waiting for IAM propagation..."); time.sleep(12)
except ClientError as e:
    if e.response["Error"]["Code"] != "EntityAlreadyExists":
        raise
    role = iam.get_role(RoleName=ROLE_NAME)["Role"]

for name, cfg in FUNCTIONS.items():
    code = LIGHT if name.endswith("light") else COMPUTE
    try:
        lam.create_function(
            FunctionName=name, Runtime="python3.12", Role=role["Arn"], Handler="app.handler",
            Code={"ZipFile": zip_code(code)}, MemorySize=cfg["memory"], Timeout=cfg["timeout"],
            Architectures=["x86_64"], Tags={"Project": "cloudcost-ai"},
        )
        print(f"Created {name} ({cfg['memory']} MB)")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise
        print(f"{name} already exists")
    lg = f"/aws/lambda/{name}"
    try:
        logs.create_log_group(logGroupName=lg)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
            raise
    logs.put_retention_policy(logGroupName=lg, retentionInDays=7)   # no unbounded log retention
print("Done. Next: python scripts/generate_load.py")
