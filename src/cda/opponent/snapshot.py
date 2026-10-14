"""对手建模：从全市场快照（MarketResult）构建对手档案。

由于结果导出包含全部公司的决策（显式博弈），本模块直接观测对手的
相对价格/广告/渠道/研发/份额，做类型识别与情景分析。
"""
from __future__ import annotations

from ..schemas import CompanyResult, MarketResult
from .profiling import OpponentProfile, OpponentStyle, classify_style


def build_opponent_profiles(
    market_result: MarketResult,
    our_company: str,
    history: dict[str, list[MarketResult]] | None = None,
) -> list[OpponentProfile]:
    """从快照构建对手档案。history 可选，用于跨回合趋势。"""
    profiles: list[OpponentProfile] = []
    for c in market_result.opponents(our_company):
        p = OpponentProfile(name=c.company)
        # 记录近期动作
        p.recent_actions.append(f"EU广告={c.advertising.get('EU', 0.0):.0f}")
        p.recent_actions.append(f"EU渠道={c.channel_investment.get('EU', 0.0):.0f}")
        p.recent_actions.append(f"研发={c.rd_investment:.0f}")
        # 份额历史（跨市场平均）
        if c.shares:
            p.record_share(sum(c.shares.values()) / len(c.shares))
        # 历史趋势
        if history:
            for snap in history:
                prev = snap.company(c.company)
                if prev and prev.shares:
                    p.record_share(sum(prev.shares.values()) / len(prev.shares))
        p.style = classify_style(p.share_history)
        p.notes = f"价格数={len(c.prices)}, 利润={c.profit:.0f}"
        profiles.append(p)
    return profiles
