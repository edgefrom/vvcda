"""贝叶斯线性回归：市场调研先验 + 系数置信区间。

样本极少（~160 观测）时，先验相当于「白送的数据」。用共轭正态先验
得到解析后验（无需 MCMC），输出系数后验均值与置信区间。

升级路径见 docs/technical/modeling-decisions.md D1/D5。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..schemas import MarketResearch


@dataclass
class BayesianLinearModel:
    mean: np.ndarray  # 系数后验均值
    cov: np.ndarray  # 系数后验协方差
    feature_names: list[str]
    noise_var: float

    def predict(self, x: np.ndarray) -> tuple[float, float]:
        """返回 (预测均值, 预测标准差)。"""
        x = np.asarray(x, dtype=float)
        mean = float(x @ self.mean)
        std = float(np.sqrt(x @ self.cov @ x + self.noise_var))
        return mean, std

    def coefficient_intervals(self, z: float = 1.96) -> dict[str, tuple[float, float]]:
        stds = np.sqrt(np.diag(self.cov))
        return {
            n: (float(self.mean[i] - z * stds[i]), float(self.mean[i] + z * stds[i]))
            for i, n in enumerate(self.feature_names)
        }


def bayesian_linear_fit(
    x: np.ndarray,
    y: np.ndarray,
    *,
    prior_mean: np.ndarray | None = None,
    prior_precision: float = 1e-3,
    noise_var: float = 1.0,
    feature_names: list[str] | None = None,
) -> BayesianLinearModel:
    """共轭正态先验的贝叶斯线性回归。

    prior_mean: 系数先验均值（长度 = 特征数）。
    prior_precision: 先验精度（越大 = 越信任先验 = 系数收缩越强）。
    noise_var: 观测噪声方差。
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n, p = x.shape
    if prior_mean is None:
        prior_mean = np.zeros(p)
    prior_mean = np.asarray(prior_mean, dtype=float)
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(p)]
    lam = np.eye(p) * prior_precision
    precision = x.T @ x / noise_var + lam
    cov = np.linalg.inv(precision)
    mean = cov @ (x.T @ y / noise_var + lam @ prior_mean)
    return BayesianLinearModel(mean=mean, cov=cov, feature_names=feature_names, noise_var=noise_var)


# 缺省先验均值（符号由经济学/市场调研确定，大小保守）
DEFAULT_PRIOR = {
    "rel_price": -2.0,  # 相对价格越高，份额越低
    "rel_ad": 0.1,  # 相对广告越高，份额越高
    "rel_channel": 0.05,
    "thinness": 0.01,
    "battery": 0.01,
    "n_features": 0.05,
}


def prior_from_research(
    research: MarketResearch | None,
    market: str,
    feature_names: list[str],
) -> np.ndarray:
    """把市场调研先验映射为系数先验均值（符号正确 + 相对大小）。

    - rel_price 的绝对值随该市场平均价格敏感度放大；
    - rel_ad 的绝对值随平均广告效果放大；
    - 其余用缺省符号。
    """
    out = [DEFAULT_PRIOR.get(n, 0.0) for n in feature_names]
    if research is not None:
        segs = [s for s in research.segments if s.market == market]
        if segs:
            avg_price_sens = sum(s.price_sensitivity for s in segs) / len(segs)
            avg_ad = sum(s.ad_effectiveness for s in segs) / len(segs)
            for i, n in enumerate(feature_names):
                if n == "rel_price":
                    out[i] = -abs(DEFAULT_PRIOR["rel_price"]) * max(avg_price_sens, 0.5) / 2.5
                elif n == "rel_ad":
                    out[i] = DEFAULT_PRIOR["rel_ad"] * max(avg_ad, 0.1) / 1.0
    return np.asarray(out, dtype=float)
