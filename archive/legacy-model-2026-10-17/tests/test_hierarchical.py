"""分层搜索测试。"""
from __future__ import annotations

from cda.optimize import hierarchical_search


def test_hierarchical_search_picks_best_portfolio() -> None:
    portfolios = [{}, {"premium": 1}]
    bounds = {"x": (-5.0, 5.0)}

    def portfolio_score(combo: dict[str, float]) -> float:
        return 0.0 if combo else 10.0  # 空组合有固定罚分

    def continuous_objective(combo: dict[str, float], d: dict[str, float]) -> float:
        return (d["x"] - 3.0) ** 2

    result = hierarchical_search(portfolios, bounds, portfolio_score, continuous_objective=continuous_objective, maxiter=100)
    assert result.portfolio == {"premium": 1}
    assert result.objective < 10.0
    assert result.continuous is not None
    assert abs(result.continuous.best["x"] - 3.0) < 0.05
