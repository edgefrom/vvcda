"""跨市场分析：批量加载多赛区结果 + 分细分弹性估计 + 盈利密码检查。

把「讨论结果」沉淀为可复用的算法：
1. 分细分价格/广告/渠道弹性（用全部赛区的截面数据拟合，比单赛区稳健）；
2. 盈利密码检查（产品覆盖、份额、广告克制、收入覆盖成本）。
"""
from __future__ import annotations

import glob
from math import log

import numpy as np

from .adapters.xls_source import parse_results
from .schemas import CompanyResult, MarketResult, SEGMENTS_DEFAULT

SEGMENTS = list(SEGMENTS_DEFAULT)


def load_all_markets(pattern: str) -> list[MarketResult]:
    """批量加载所有赛区结果文件（跳过解析失败的）。"""
    files = sorted(glob.glob(pattern, recursive=True))
    out: list[MarketResult] = []
    for f in files:
        try:
            out.append(parse_results(f))
        except Exception:
            continue
    return out


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return log(p / (1 - p))


def _avg_price(c: CompanyResult, market: str) -> float:
    ps = [v for k, v in c.prices.items() if k.startswith(market + ":") and v > 0]
    return sum(ps) / len(ps) if ps else 0.0


def fit_segment_elasticities(markets: list[MarketResult], market: str = "EU") -> dict[str, dict[str, float]]:
    """分细分拟合 logit(份额) = 截距 + β价·相对价格 + β广·相对广告 + β渠·相对渠道。

    返回 {细分: {"intercept", "rel_price", "rel_ad", "rel_channel", "n"}}。
    """
    out: dict[str, dict[str, float]] = {}
    for seg in SEGMENTS:
        rows: list[list[float]] = []
        ys: list[float] = []
        for m in markets:
            prices = [_avg_price(c, market) for c in m.companies]
            mp = float(np.mean([p for p in prices if p > 0])) or 1.0
            ads = [c.advertising.get(market, 0.0) for c in m.companies]
            ma = float(np.mean([a for a in ads if a > 0])) or 1.0
            chs = [c.channel_investment.get(market, 0.0) for c in m.companies]
            mc = float(np.mean([v for v in chs if v > 0])) or 1.0
            for c in m.companies:
                share = c.shares.get(f"{market}:{seg}", 0.0)
                if 0.0 < share < 100.0:
                    ap = _avg_price(c, market) or mp
                    rows.append([1.0, ap / mp, c.advertising.get(market, 0.0) / ma, c.channel_investment.get(market, 0.0) / mc])
                    ys.append(_logit(share / 100.0))
        if len(ys) < 10:
            continue
        x = np.asarray(rows)
        y = np.asarray(ys)
        coef, *_ = np.linalg.lstsq(x, y, rcond=None)
        out[seg] = {
            "intercept": float(coef[0]),
            "rel_price": float(coef[1]),
            "rel_ad": float(coef[2]),
            "rel_channel": float(coef[3]),
            "n": int(len(ys)),
        }
    return out


def profitable_check(c: CompanyResult, market: str = "EU") -> dict[str, float]:
    """盈利密码检查：对照盈利队伍的画像，给出差距诊断。"""
    n_products = len([k for k in c.prices if k.startswith(market + ":")])
    share = sum(c.shares.get(f"{market}:{seg}", 0.0) for seg in SEGMENTS) / len(SEGMENTS)
    ad = c.advertising.get(market, 0.0)
    return {
        "n_products": float(n_products),
        "avg_share_pct": share,
        "advertising": ad,
        "revenue": c.revenue,
        "profit": c.profit,
        "income_covers_cost": 1.0 if c.profit > 0 else 0.0,
    }


def benchmark_profitable(markets: list[MarketResult], market: str = "EU") -> dict[str, float]:
    """汇总所有盈利公司的画像，作为「盈利基准」。"""
    prof = [c for m in markets for c in m.companies if c.profit > 0]
    if not prof:
        return {}
    shares = [sum(c.shares.get(f"{market}:{seg}", 0.0) for seg in SEGMENTS) / len(SEGMENTS) for c in prof]
    nprods = [len([k for k in c.prices if k.startswith(market + ":")]) for c in prof]
    ads = [c.advertising.get(market, 0.0) for c in prof]
    return {
        "count": float(len(prof)),
        "avg_share_pct": float(np.mean(shares)),
        "avg_n_products": float(np.mean(nprods)),
        "avg_advertising": float(np.mean(ads)),
        "median_revenue": float(np.median([c.revenue for c in prof])),
    }
