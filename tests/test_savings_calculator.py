import pytest

from engine import savings_calculator as sc


def test_monthly_cost_known_value():
    # 1 GB x 1 s x 1M invocations = 1M GB-s -> 16.6667 + $0.20 request charge
    assert sc.monthly_cost(1024, 1000, 1_000_000) == pytest.approx(16.8667, abs=1e-3)


def test_arm_is_cheaper():
    assert sc.monthly_cost(1024, 1000, 1_000_000, "arm64") < sc.monthly_cost(1024, 1000, 1_000_000, "x86_64")


def test_savings_and_annual_is_12x():
    r = sc.estimate_savings(1024, 256, 1000, 1_000_000)
    assert r["monthly_savings"] == pytest.approx(12.5, abs=1e-3)
    assert r["annual_savings"] == pytest.approx(12 * r["monthly_savings"])


def test_slower_duration_can_erase_savings():
    r = sc.estimate_savings(1024, 256, 1000, 1_000_000, target_duration_ms=4000)
    assert r["monthly_savings"] == pytest.approx(0.0, abs=1e-6)


def test_monthly_invocations_scaling():
    assert sc.monthly_invocations(140, 14) == 300
    assert sc.monthly_invocations(10, 0) == 0
