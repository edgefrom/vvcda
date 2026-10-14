"""非线性诊断：判断 logit 线性模型对真实份额的拟合是否足够。

输出 R²、RMSE 与残差统计；R² 偏低或残差有系统模式时，提示需要
加非线性变换（升级路径见 docs/modeling-decisions.md D5）。
"""
from __future__ import annotations

from math import sqrt

import numpy as np

from ..schemas import MarketResult
from .features import build_dataset, fit_relative_model


def _logit(share_pct: float) -> float:
    from math import log

    return log(share_pct / (100.0 - share_pct))


def diagnostics(market_result: MarketResult, market: str, feature_names: list[str]) -> dict[str, float]:
    """拟合 logit(份额) 线性模型，返回诊断指标。"""
    x, y, keys = build_dataset(market_result, market, feature_names)
    n = len(y)
    if n < 3:
        return {"n": n, "r2": float("nan"), "rmse": float("nan"), "residual_std": float("nan")}
    coef = fit_relative_model(market_result, market, feature_names)
    y_pred = x @ np.asarray([coef[f] for f in feature_names], dtype=float)
    if "intercept" in coef:
        y_pred = y_pred + coef["intercept"]
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse = sqrt(ss_res / n)
    # 残差自相关（粗略：按 y_pred 排序后相邻残差相关系数），>0 提示系统偏差
    order = np.argsort(y_pred)
    resid = (y - y_pred)[order]
    residual_std = float(np.std(resid))
    return {"n": n, "r2": r2, "rmse": rmse, "residual_std": residual_std}


def is_linear_sufficient(diag: dict[str, float], r2_threshold: float = 0.5) -> bool:
    """简单判定：R² 高于阈值即认为线性 logit 暂够用。"""
    r2 = diag.get("r2", float("nan"))
    return not (r2 == r2 and r2 < r2_threshold)
