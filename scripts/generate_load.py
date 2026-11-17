"""Invoke each demo function a bounded number of times (Compute Optimizer needs >= 50 in 14 days).
python scripts/generate_load.py [count]   (default 60, hard cap 120)"""
import json
import sys

from _common import FUNCTIONS, session

count = min(int(sys.argv[1]) if len(sys.argv) > 1 else 60, 120)
sess, _ = session()
lam = sess.client("lambda")
for name in FUNCTIONS:
    errors = 0
    for _ in range(count):
        r = lam.invoke(FunctionName=name, Payload=json.dumps({"rounds": 250000}).encode())
        errors += 1 if r.get("FunctionError") else 0
    print(f"{name}: {count} invocations, {errors} errors")
print("Free allowance is 1M requests and 400,000 GB-s per month; this uses a tiny fraction.")
print("Compute Optimizer may take up to ~24h to show results after opting in / invoking.")
