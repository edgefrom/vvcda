"""分层搜索：产品组合（离散）→ 定价/营销（连续）的两级搜索。

决策空间是「产品组合 + 定价 + 营销」的组合优化（决策指南 §4-5）。
本模块提供两级搜索骨架：
  1. 组合层：枚举/随机搜索「每个产品投放哪些市场」的离散组合；
  2. 连续层：给定组合，用差分进化搜索价格/广告/渠道等连续变量。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .search import OptimizationResult, differential_evolution_search

PortfolioEvaluator = Callable[[dict[str, float]], float]


@dataclass
class HierarchicalResult:
    portfolio: dict[str, float]
    continuous: OptimizationResult | None = None
    objective: float = float("inf")


def hierarchical_search(
    portfolio_options: list[dict[str, float]],
    continuous_bounds: dict[str, tuple[float, float]],
    portfolio_score: PortfolioEvaluator,
    *,
    continuous_objective: Callable[[dict[str, float], dict[str, float]], float],
    seed: int = 0,
    maxiter: int = 100,
    integer_fields: tuple[str, ...] = (),
) -> HierarchicalResult:
    """两级搜索。

    portfolio_options: 候选产品组合列表（每个是离散变量字典）。
    portfolio_score: 评估某组合（不含连续变量）的基础分（如固定成本、覆盖细分）。
    continuous_objective: (组合, 连续变量) -> 标量，越小越好。
    """
    best = HierarchicalResult(portfolio={})
    for combo in portfolio_options:
        base = portfolio_score(combo)

        def inner(d: dict[str, float]) -> float:
            return base + continuous_objective(combo, d)

        result = differential_evolution_search(
            inner, continuous_bounds, seed=seed, maxiter=maxiter, integer_fields=integer_fields
        )
        if result.objective < best.objective:
            best = HierarchicalResult(portfolio=combo, continuous=result, objective=result.objective)
    return best
