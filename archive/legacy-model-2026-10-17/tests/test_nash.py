"""可插拔纳什预判测试。"""
from __future__ import annotations

import pytest

from cda.opponent.nash import nash_price_equilibrium


def test_symmetric_equilibrium_price() -> None:
    companies = ["A", "B", "C"]
    beta, unit_cost = 0.05, 100.0
    res = nash_price_equilibrium(companies, beta=beta, unit_cost=unit_cost)
    assert res.converged
    # 对称 logit 均衡理论价：p = c + n / (β(n-1)) = 100 + 3/(0.05*2) = 130
    expected = unit_cost + len(companies) / (beta * (len(companies) - 1))
    for p in res.prices.values():
        assert p == pytest.approx(expected, abs=1.5)


def test_shares_sum_to_one() -> None:
    companies = ["A", "B", "C", "D"]
    res = nash_price_equilibrium(companies, beta=0.05, unit_cost=50.0)
    assert abs(sum(res.shares.values()) - 1.0) < 1e-6
    assert all(p > 50.0 for p in res.prices.values())


def test_no_underflow_with_large_beta_and_price() -> None:
    """价格高 + 敏感度大时 exp 下溢不应导致除零。"""
    companies = ["A", "B", "C"]
    res = nash_price_equilibrium(companies, beta=3.0, unit_cost=150.0, price_upper=750.0)
    assert abs(sum(res.shares.values()) - 1.0) < 1e-6
    assert all(p > 150.0 for p in res.prices.values())
