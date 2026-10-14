"""搜索器：差分进化（基线）。

后续可替换/升级为 CMA-ES、贝叶斯优化等，保持 objective_fn 签名不变。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy import optimize as sp_optimize

ObjectiveFn = Callable[[dict[str, float]], float]


@dataclass
class OptimizationResult:
    best: dict[str, float]
    objective: float
    history: list[float] = field(default_factory=list)


def differential_evolution_search(
    objective_fn: ObjectiveFn,
    bounds: dict[str, tuple[float, float]],
    *,
    integer_fields: tuple[str, ...] = (),
    seed: int = 0,
    maxiter: int = 200,
    popsize: int = 15,
) -> OptimizationResult:
    """在给定边界内最小化 objective_fn，返回最优决策向量。

    参数
    ----
    objective_fn: 输入决策 dict -> 标量（越小越好）。
    bounds: 字段名 -> (lower, upper)。
    integer_fields: 需要取整的字段（如产量）；搜索时内部取整。
    """
    names = list(bounds)
    lo = [bounds[n][0] for n in names]
    hi = [bounds[n][1] for n in names]

    def wrapped(x: np.ndarray) -> float:
        values: dict[str, float] = {}
        for name, v in zip(names, x):
            values[name] = round(v) if name in integer_fields else float(v)
        return float(objective_fn(values))

    result = sp_optimize.differential_evolution(
        wrapped,
        list(zip(lo, hi)),
        seed=seed,
        maxiter=maxiter,
        popsize=popsize,
        polish=True,
    )
    best_values: dict[str, float] = {}
    for name, v in zip(names, result.x):
        best_values[name] = round(v) if name in integer_fields else float(v)
    return OptimizationResult(best=best_values, objective=float(result.fun))
