"""蒙特卡洛情景评估：在参数不确定下评估决策的稳健性。

不做「精确预测第一名概率」——那在参数未知 + 自适应对手下是噪音。
这里只给出代理目标的分布（均值/分位数），帮人排除明显坏招。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..demand.base import DemandModel
from ..schemas import DecisionVector, Financials, SegmentOutcome
from .objectives import ProxyObjective


@dataclass
class Scenario:
    """一个市场情景：需求模型 + 各细分市场规模。"""

    demand: DemandModel
    market_sizes: dict[tuple[str, str], float]


@dataclass
class FinancialModel:
    """极简财务模型（先验模板，拿到真实成本结构后替换）。

    - 需求 = Σ 细分 share × 市场规模
    - 产量不足时按比例缺货（fill_rate = min(1, 产量/需求)），即「产量报少了是丢单」
    - 成本 = 产量 × 单位成本 + 固定成本 + Σ 费用字段（广告/研发等现金支出）
    """

    unit_cost: float = 1.0
    fixed_cost: float = 0.0
    production_field: str = "production_qty"
    price_fields: dict[str, str] = field(default_factory=lambda: {"EU": "price_EU", "ASIA": "price_ASIA"})
    expense_fields: list[str] = field(default_factory=list)  # 作为现金费用计入成本

    def simulate(self, decision: DecisionVector, outcomes: list[SegmentOutcome]) -> Financials:
        total_demand = sum(o.our_sales for o in outcomes)
        produced = decision.get(self.production_field, 0.0)
        fill_rate = min(1.0, produced / total_demand) if total_demand > 0 else 0.0
        revenue = 0.0
        sold_total = 0.0
        for o in outcomes:
            sold = o.our_sales * fill_rate
            price_field = self.price_fields.get(o.market)
            price = decision.get(price_field, 0.0) if price_field else 0.0
            revenue += sold * price
            sold_total += sold
        expenses = sum(decision.get(f, 0.0) for f in self.expense_fields)
        cost = produced * self.unit_cost + self.fixed_cost + expenses
        return Financials(
            revenue=revenue,
            cost=cost,
            profit=revenue - cost,
            cash=0.0,
            inventory=max(0.0, produced - sold_total),
        )


@dataclass
class EvaluationResult:
    scores: list[float]
    mean: float
    p10: float
    p90: float

    def summary(self) -> str:
        return f"目标均值 {self.mean:.3f}（P10 {self.p10:.3f} ~ P90 {self.p90:.3f}，n={len(self.scores)}）"


def make_scenarios(
    base_demand: DemandModel,
    markets_segments: list[tuple[str, str]],
    *,
    noise_std: float = 0.1,
    n_scenarios: int = 200,
    market_sizes: dict[tuple[str, str], float] | None = None,
    rng: np.random.Generator | None = None,
) -> list[Scenario]:
    """在基线需求模型上加噪声，生成情景集（模拟参数不确定）。

    noise_std 作用于 logit 层面，代表对需求参数的不确定。
    """
    rng = rng if rng is not None else np.random.default_rng(0)
    sizes = market_sizes or {ms: 1.0 for ms in markets_segments}

    class _Perturbed(DemandModel):
        def __init__(self, base: DemandModel, shock: dict[tuple[str, str], float]) -> None:
            self._base = base
            self._shock = shock

        def predict_share(self, decision: DecisionVector, market: str, segment: str) -> float:
            import math
            base = self._base.predict_share(decision, market, segment)
            z = math.log(max(base, 1e-9) / (1.0 - max(base, 1e-9)))
            z += self._shock.get((market, segment), 0.0)
            z = max(-50.0, min(50.0, z))
            return 1.0 / (1.0 + math.exp(-z))

    scenarios: list[Scenario] = []
    for _ in range(n_scenarios):
        shock = {ms: float(rng.normal(0.0, noise_std)) for ms in markets_segments}
        scenarios.append(Scenario(demand=_Perturbed(base_demand, shock), market_sizes=dict(sizes)))
    return scenarios


def evaluate_decision(
    decision: DecisionVector,
    scenarios: list[Scenario],
    financial_model: FinancialModel,
    objective: ProxyObjective | None = None,
) -> EvaluationResult:
    """在情景集上评估决策，返回代理目标分布。"""
    objective = objective or ProxyObjective()
    scores: list[float] = []
    for sc in scenarios:
        outcomes: list[SegmentOutcome] = []
        for (market, segment), size in sc.market_sizes.items():
            share = sc.demand.predict_share(decision, market, segment)
            sales = share * size
            outcomes.append(SegmentOutcome(market=market, segment=segment, our_sales=sales, market_sales=size, our_share=share))
        fin = financial_model.simulate(decision, outcomes)
        scores.append(objective.score(fin, outcomes))
    arr = np.asarray(scores)
    return EvaluationResult(
        scores=scores,
        mean=float(arr.mean()),
        p10=float(np.percentile(arr, 10)),
        p90=float(np.percentile(arr, 90)),
    )
