"""贝叶斯线性回归测试。"""
from __future__ import annotations

import numpy as np

from cda.demand.bayes import bayesian_linear_fit, prior_from_research


def test_bayesian_fit_recovers_and_interval_covers() -> None:
    rng = np.random.default_rng(0)
    n, p = 200, 2
    x = rng.normal(size=(n, p))
    true = np.array([1.5, -2.0])
    y = x @ true + rng.normal(0.0, 0.5, size=n)
    model = bayesian_linear_fit(x, y, prior_precision=1e-3, noise_var=0.25, feature_names=["a", "b"])
    assert np.allclose(model.mean, true, atol=0.15)
    intervals = model.coefficient_intervals()
    for i, name in enumerate(["a", "b"]):
        lo, hi = intervals[name]
        assert lo <= true[i] <= hi


def test_strong_prior_shrinks_coefficient() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=(5, 1))
    y = x @ np.array([10.0]) + rng.normal(0.0, 0.1, size=5)
    strong = bayesian_linear_fit(x, y, prior_mean=np.array([0.0]), prior_precision=1.0, noise_var=0.01, feature_names=["x"])
    weak = bayesian_linear_fit(x, y, prior_mean=np.array([0.0]), prior_precision=1e-4, noise_var=0.01, feature_names=["x"])
    assert abs(strong.mean[0]) < abs(weak.mean[0])  # 强先验 → 更收缩到 0


def test_prior_from_research_signs() -> None:
    pri = prior_from_research(None, "EU", ["rel_price", "rel_ad", "rel_channel"])
    assert pri[0] < 0  # 价格系数为负
    assert pri[1] > 0  # 广告为正
    assert pri[2] > 0  # 渠道为正
