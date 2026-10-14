"""递归最小二乘（在线更新）测试。"""
from __future__ import annotations

import numpy as np

from cda.demand.online import RecursiveLeastSquares


def test_rls_converges_to_ols() -> None:
    rng = np.random.default_rng(0)
    n, p = 300, 3
    x = rng.normal(size=(n, p))
    true = np.array([1.0, -2.0, 0.5])
    y = x @ true + rng.normal(0.0, 0.2, size=n)
    rls = RecursiveLeastSquares(p, forgetting=1.0)
    for i in range(n):
        rls.update(x[i], y[i])
    ols, *_ = np.linalg.lstsq(x, y, rcond=None)
    assert np.allclose(rls.coefficients, ols, atol=0.05)


def test_rls_forgetting_prefers_recent() -> None:
    no_forget = RecursiveLeastSquares(1, forgetting=1.0)
    forget = RecursiveLeastSquares(1, forgetting=0.5)
    for _ in range(50):
        no_forget.update(np.array([1.0]), 0.0)
        forget.update(np.array([1.0]), 0.0)
    for _ in range(50):
        no_forget.update(np.array([1.0]), 10.0)
        forget.update(np.array([1.0]), 10.0)
    # 无遗忘 → 两段各半，系数≈5；有遗忘 → 偏向近期 10，应明显 > 5
    assert abs(no_forget.coefficients[0] - 5.0) < 0.2
    assert forget.coefficients[0] > 6.0
