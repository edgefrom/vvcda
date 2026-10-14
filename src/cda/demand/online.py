"""递归最小二乘（RLS）：每回合增量吸收新观测，无需重跑全部历史。"""
from __future__ import annotations

import numpy as np


class RecursiveLeastSquares:
    """带遗忘因子的 RLS。新数据权重更高，旧数据随时间衰减。"""

    def __init__(self, n_features: int, forgetting: float = 0.995, delta: float = 1e3) -> None:
        self.w = np.zeros(n_features, dtype=float)
        self.P = np.eye(n_features, dtype=float) * delta
        self.forgetting = forgetting

    def update(self, x: np.ndarray, y: float) -> None:
        x = np.asarray(x, dtype=float)
        px = self.P @ x
        denom = self.forgetting + float(x @ px)
        k = px / denom
        error = y - float(x @ self.w)
        self.w = self.w + k * error
        self.P = (self.P - np.outer(k, px)) / self.forgetting

    @property
    def coefficients(self) -> np.ndarray:
        return self.w.copy()

    def predict(self, x: np.ndarray) -> float:
        return float(np.asarray(x, dtype=float) @ self.w)
