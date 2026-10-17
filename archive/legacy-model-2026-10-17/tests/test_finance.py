"""财务仿真（损益表 + 亏损结转）测试。"""
from __future__ import annotations

from cda.eval.finance import IncomeStatement, TaxTracker


def test_income_statement_flow() -> None:
    stmt = IncomeStatement(revenue=1000.0, service_revenue=100.0, variable_cost=400.0, fixed_cost=300.0)
    assert stmt.gross_profit == 700.0
    assert stmt.operating_profit == 400.0
    assert stmt.pretax_profit == 400.0


def test_income_statement_with_interest() -> None:
    stmt = IncomeStatement(revenue=1000.0, variable_cost=400.0, fixed_cost=300.0, interest_income=50.0, interest_expense=20.0)
    assert stmt.pretax_profit == 330.0


def test_tax_tracker_profit() -> None:
    tracker = TaxTracker(tax_rate=0.25)
    net = tracker.net_profit(100.0)
    assert net == 75.0


def test_tax_tracker_loss_carryforward() -> None:
    tracker = TaxTracker(tax_rate=0.25)
    # 第一回合亏损 100
    net1 = tracker.net_profit(-100.0)
    assert net1 == -100.0
    assert tracker.carryforward == 100.0
    # 第二回合盈利 100：先用 100 亏损抵扣 → 应税 0 → 净利润 100
    net2 = tracker.net_profit(100.0)
    assert net2 == 100.0
    assert tracker.carryforward == 0.0


def test_tax_tracker_partial_carryforward() -> None:
    tracker = TaxTracker(tax_rate=0.25)
    tracker.net_profit(-100.0)  # 结转 100
    # 盈利 50：抵扣 50，应税 0，结转剩 50
    net = tracker.net_profit(50.0)
    assert net == 50.0
    assert tracker.carryforward == 50.0
