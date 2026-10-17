"""财务模型与情景评估的测试。"""
from __future__ import annotations

from cda.eval import FinancialModel, ProxyObjective, evaluate_decision, make_scenarios
from cda.demand import LogitDemandModel
from cda.schemas import DecisionVector, SegmentOutcome


def test_stockout_scales_revenue_and_sets_zero_inventory() -> None:
    fin = FinancialModel(unit_cost=0.5, price_fields={"EU": "price_EU"})
    decision = DecisionVector(turn=0, values={"price_EU": 100.0, "production_qty": 50.0})
    outcomes = [SegmentOutcome(market="EU", segment="consumer", our_sales=200.0, market_sales=1000.0, our_share=0.2)]
    result = fin.simulate(decision, outcomes)
    # 产量 50 < 需求 200 → fill_rate=0.25 → 卖出 50，收入 5000
    assert result.revenue == 5000.0
    assert result.inventory == 0.0


def test_expenses_are_subtracted_from_profit() -> None:
    fin = FinancialModel(unit_cost=0.0, expense_fields=["advertising_EU"])
    decision = DecisionVector(turn=0, values={"price_EU": 100.0, "production_qty": 1000.0, "advertising_EU": 30.0})
    outcomes = [SegmentOutcome(market="EU", segment="consumer", our_sales=10.0, market_sales=1000.0, our_share=0.01)]
    result = fin.simulate(decision, outcomes)
    assert result.cost == 30.0
    assert result.profit == 1000.0 - 30.0


def test_evaluate_decision_produces_distribution() -> None:
    model = LogitDemandModel(
        segment_intercepts={("EU", "consumer"): -1.0},
        feature_betas={"price_EU": -0.01},
    )
    scenarios = make_scenarios(model, [("EU", "consumer")], noise_std=0.05, n_scenarios=50)
    fin = FinancialModel(unit_cost=0.5)
    decision = DecisionVector(turn=0, values={"price_EU": 300.0, "production_qty": 1000.0})
    res = evaluate_decision(decision, scenarios, fin)
    assert len(res.scores) == 50
    assert res.p10 <= res.mean <= res.p90


def test_proxy_objective_growth_term() -> None:
    from cda.schemas import Financials

    obj = ProxyObjective(weights={"profit": 1.0, "share": 0.0, "growth": 1.0}, previous_profit=100.0)
    fin = Financials(revenue=200.0, cost=100.0, profit=100.0)
    score = obj.score(fin, [SegmentOutcome(market="EU", segment="consumer", our_share=0.5)])
    # profit=100, growth=(100-100)/100=0 → score = 100
    assert score == 100.0
