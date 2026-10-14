"""对手建模：类型识别与档案。

诚实说明：9 个自适应人类对手无法精确预测；本模块只做「有限博弈思维」的
辅助——类型标签 + 近期动作记录 + 简单启发式分类，用于防守（不被偷袭），
而非精确预测对手决策。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class OpponentStyle(str, Enum):
    AGGRESSIVE = "aggressive"  # 激进：降价、高投入
    FOLLOWER = "follower"  # 模仿者：追涨杀跌
    STEADY = "steady"  # 稳健派
    UNKNOWN = "unknown"


@dataclass
class OpponentProfile:
    """一家对手公司的档案。"""

    name: str
    style: OpponentStyle = OpponentStyle.UNKNOWN
    share_history: list[float] = field(default_factory=list)
    recent_actions: list[str] = field(default_factory=list)
    notes: str = ""

    def record_share(self, share: float) -> None:
        self.share_history.append(share)

    def record_action(self, action: str) -> None:
        self.recent_actions.append(action)


def classify_style(share_history: list[float], price_history: list[float] | None = None) -> OpponentStyle:
    """简单启发式分类。数据不足时返回 UNKNOWN。

    启发式：
    - 份额波动大且价格持续下降 → 激进；
    - 份额波动大但价格变化无方向 → 模仿者；
    - 波动小 → 稳健；
    - 数据不足 → 未知。
    """
    if len(share_history) < 3:
        return OpponentStyle.UNKNOWN
    shares = [s for s in share_history if s is not None]
    if len(shares) < 3:
        return OpponentStyle.UNKNOWN

    spread = max(shares) - min(shares)
    mean = sum(shares) / len(shares)
    volatility = spread / mean if mean > 0 else 1.0

    if price_history and len(price_history) >= 2:
        prices = [p for p in price_history if p is not None]
        if len(prices) >= 2 and prices[-1] < prices[0]:
            if volatility > 0.3:
                return OpponentStyle.AGGRESSIVE
    if volatility > 0.3:
        return OpponentStyle.FOLLOWER
    return OpponentStyle.STEADY
