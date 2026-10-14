"""目标函数：股价的代理目标（proxy）。

真实股价函数是黑箱，拿到足够回合差分数据后才能校准。在此之前用
可解释的代理目标：利润 + 份额 + 增长 的加权组合（越小越差，见 note）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..schemas import Financials, SegmentOutcome


@dataclass
class ProxyObjective:
    """加权代理目标。权重可配置；默认：利润为主，份额次之。"""

    weights: dict[str, float] = field(
        default_factory=lambda: {"profit": 1.0, "share": 0.3, "growth": 0.2}
    )
    previous_profit: float = 0.0  # 用于计算增长；首回合为 0

    def score(self, financials: Financials, outcomes: list[SegmentOutcome]) -> float:
        profit = financials.profit
        total_share = sum(o.our_share for o in outcomes) / max(len(outcomes), 1)
        growth = (profit - self.previous_profit) / max(abs(self.previous_profit), 1.0)
        return (
            self.weights.get("profit", 0.0) * profit
            + self.weights.get("share", 0.0) * total_share
            + self.weights.get("growth", 0.0) * growth
        )


def weighted_objective(
    financials: Financials,
    outcomes: list[SegmentOutcome],
    weights: dict[str, float] | None = None,
    previous_profit: float = 0.0,
) -> float:
    obj = ProxyObjective(weights=weights or {"profit": 1.0, "share": 0.3, "growth": 0.2}, previous_profit=previous_profit)
    return obj.score(financials, outcomes)
