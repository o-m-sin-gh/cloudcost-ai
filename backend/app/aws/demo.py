"""Demo provider: sample data so the whole app works with NO AWS account.

Everything returned here is labelled mode="demo" / source="demo" and the UI shows
a DEMO banner. Never present this data as real AWS data.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

# name, memory, timeout, arch, avg_ms@initial_mem, invocations/day, cpu_sensitivity, max_mem_used, ideal_mem
_SEED = [
    ("cloudcost-demo-light",         1024, 10, "x86_64", 128,  170, 0.05,  78,  256),
    ("cloudcost-demo-compute",        256, 30, "x86_64", 2100, 130, 0.90, 250, 1024),
    ("cloudcost-demo-api-handler",    512,  5, "arm64",   85,  640, 0.30, 410,  512),
    ("cloudcost-demo-cron-cleanup",   512, 60, "x86_64", 300,   28, 0.10,  60,  128),
    ("cloudcost-demo-image-resizer", 2048, 30, "x86_64", 900,   75, 0.80, 700, 2048),
    ("cloudcost-demo-batch-report",  1536, 60, "x86_64", 450,    3, 0.20, 300,  384),
    ("orders-prod-processor",        1024, 15, "x86_64", 150,  300, 0.10,  90,  256),  # outside managed scope
]


class DemoProvider:
    mode = "demo"

    def __init__(self):
        self.fns = {}
        for name, mem, to, arch, ms, per_day, sens, used, ideal in _SEED:
            self.fns[name] = dict(
                name=name, arn=f"arn:aws:lambda:ap-south-1:000000000000:function:{name}",
                runtime="python3.12", memory_mb=mem, timeout_s=to, architecture=arch,
                last_modified="2026-11-01T10:00:00.000+0000", state="Active",
                last_update_status="Successful",
                _base_ms=ms, _base_mem=mem, _per_day=per_day, _sens=sens, _used=used, _ideal=ideal,
            )
        self.changes: dict[str, list[tuple[datetime, int]]] = {n: [] for n in self.fns}

    # ---- helpers -------------------------------------------------------
    @staticmethod
    def _public(f: dict) -> dict:
        return {k: v for k, v in f.items() if not k.startswith("_")}

    def _duration_at(self, f: dict, mem: int) -> float:
        """CPU scales with memory below ~1769 MB, so CPU-bound code slows when memory drops."""
        eff = min(mem, 1769)
        base_eff = min(f["_base_mem"], 1769)
        return f["_base_ms"] * (base_eff / eff) ** f["_sens"]

    def _mem_at(self, name: str, ts: datetime) -> int:
        mem = self.fns[name]["_base_mem"]
        for when, m in self.changes[name]:
            if ts >= when:
                mem = m
        return mem

    # ---- interface -----------------------------------------------------
    def identity(self) -> dict:
        return {"account_id": "000000000000", "arn": "arn:aws:iam::000000000000:user/demo-user",
                "region": "ap-south-1", "mode": "demo"}

    def list_functions(self) -> list[dict]:
        return [self._public(f) for f in self.fns.values()]

    def get_function(self, name: str) -> dict:
        if name not in self.fns:
            raise KeyError(name)
        return self._public(self.fns[name])

    def get_metrics(self, name: str, start: datetime, end: datetime, period: int = 86400) -> dict:
        f = self.fns[name]
        changes = self.changes[name]
        # Demo fast-forward: a window that starts after a change is treated as >= 1 day of traffic.
        if changes and start >= changes[-1][0] - timedelta(seconds=1):
            end = max(end, start + timedelta(days=1))
            period = 3600
        rng = random.Random(f"{name}-{int(start.timestamp() // 3600) if not changes else 'post'}")
        series, t, total, weighted, mx, errs = [], start, 0, 0.0, 0.0, 0
        while t < end:
            mem = self._mem_at(name, t)
            n = max(0, int(f["_per_day"] * period / 86400 * rng.uniform(0.8, 1.2)))
            avg = self._duration_at(f, mem) * rng.uniform(0.95, 1.05)
            e = 1 if (n > 50 and rng.random() < 0.15) else 0
            total += n; weighted += n * avg; mx = max(mx, avg * 1.6); errs += e
            series.append({"ts": t.isoformat(), "invocations": n, "avg_duration_ms": round(avg, 2),
                           "max_duration_ms": round(avg * 1.6, 2), "errors": e})
            t += timedelta(seconds=period)
        return {
            "function": name, "source": "demo",
            "period_days": round((end - start).total_seconds() / 86400, 3),
            "invocations": total, "errors": errs, "throttles": 0,
            "avg_duration_ms": round(weighted / total, 2) if total else 0.0,
            "max_duration_ms": round(mx, 2), "max_concurrent": 3, "series": series,
        }

    def get_max_memory_used(self, name: str, start: datetime, end: datetime) -> int | None:
        return self.fns[name]["_used"]

    def get_recommendations(self) -> dict:
        items = []
        for f in self.fns.values():
            n14 = f["_per_day"] * 14
            base = dict(function_name=f["name"], arn=f["arn"], source="demo-sample",
                        current_memory_mb=f["memory_mb"], number_of_invocations=n14, lookback_days=14,
                        aws_monthly_savings_usd=None, performance_risk=None, recommended_memory_mb=None)
            if f["memory_mb"] > 1792:
                items.append({**base, "finding": "Unavailable", "reason_codes": ["Inconclusive"]})
            elif n14 < 50:
                items.append({**base, "finding": "Unavailable", "reason_codes": ["InsufficientData"]})
            elif f["memory_mb"] == f["_ideal"]:
                items.append({**base, "finding": "Optimized", "reason_codes": [], "recommended_memory_mb": f["memory_mb"]})
            else:
                code = "MemoryOverprovisioned" if f["memory_mb"] > f["_ideal"] else "MemoryUnderprovisioned"
                items.append({**base, "finding": "NotOptimized", "reason_codes": [code],
                              "recommended_memory_mb": f["_ideal"],
                              "performance_risk": 3.0 if code == "MemoryUnderprovisioned" else 0.0})
        return {"status": "ok", "message": "Sample recommendations (demo mode, not from AWS).", "items": items}

    def update_memory(self, name: str, memory_mb: int) -> dict:
        f = self.fns[name]
        f["memory_mb"] = int(memory_mb)
        f["last_modified"] = datetime.now(timezone.utc).isoformat()
        self.changes[name].append((datetime.now(timezone.utc), int(memory_mb)))
        return {"request_id": "demo-request", "memory_mb": int(memory_mb), "last_update_status": "Successful"}
