"""可插拔纳什预判（防御性工具，默认不启用）。

用途：万一对手也在用类似的量化模型（理性优化），预判他们可能收敛到的
价格，作为「最坏情景」之一输入优化器。注意局限（docs/technical/modeling-decisions.md D1）：
对手大多非完全理性，纳什预判只作情景参考，不作为主策略。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import exp

import numpy as np
from scipy import optimize as sp_optimize


@dataclass
class NashPriceResult:
    prices: dict[str, float] = field(default_factory=dict)
    shares: dict[str, float] = field(default_factory=dict)
    converged: bool = False
    iterations: int = 0


def _shares(prices: list[float], beta: float) -> list[float]:
    # log-sum-exp 稳定化：避免 exp(-β·p) 在价格大/敏感度高时下溢为 0
    log_att = [-beta * p for p in prices]
    max_log = max(log_att)
    att = [exp(l - max_log) for l in log_att]
    total = sum(att)
    return [a / total for a in att]


def nash_price_equilibrium(
    companies: list[str],
    beta: float,
    unit_cost: float,
    *,
    price_lower: float | None = None,
    price_upper: float | None = None,
    max_iter: int = 50,
    tol: float = 1e-4,
    seed: int = 0,
) -> NashPriceResult:
    """对单市场单变量（价格）的 logit 份额模型求迭代 best response 均衡。

    模型：share_i = exp(-β·p_i) / Σ exp(-β·p_j)，利润_i = share_i × (p_i − c)。
    每个公司固定他人价格、对自己的价格做一维最优反应，循环直至收敛。
    """
    rng = np.random.default_rng(seed)
    lo = price_lower if price_lower is not None else unit_cost * 1.01
    hi = price_upper if price_upper is not None else unit_cost * 5.0
    prices = [float(rng.uniform(lo, hi)) for _ in companies]

    def best_response(others: list[float]) -> float:
        def neg_profit(p: float) -> float:
            all_prices = others + [p]
            s = _shares(all_prices, beta)[-1]
            return -s * (p - unit_cost)

        res = sp_optimize.minimize_scalar(neg_profit, bounds=(lo, hi), method="bounded")
        return float(res.x)

    converged = False
    for it in range(max_iter):
        new_prices = list(prices)
        max_change = 0.0
        for i in range(len(companies)):
            others = [new_prices[j] for j in range(len(companies)) if j != i]
            new_prices[i] = best_response(others)
            max_change = max(max_change, abs(new_prices[i] - prices[i]))
        prices = new_prices
        if max_change < tol:
            converged = True
            break

    shares = _shares(prices, beta)
    return NashPriceResult(
        prices={c: prices[i] for i, c in enumerate(companies)},
        shares={c: shares[i] for i, c in enumerate(companies)},
        converged=converged,
        iterations=it + 1,
    )
