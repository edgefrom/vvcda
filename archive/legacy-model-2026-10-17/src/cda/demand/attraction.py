"""Logit 吸引力需求模型（基线）。

模型假设（与机制说明书 §5 的「吸引力竞争」推断一致）：

    share = sigmoid(logit)，  logit = 细分截距 + Σ 特征弹性 × 特征值

即 logit(share) = a_{m,s} + Σ_k β_k · x_k。竞争对手的聚合强度被吸收进
细分截距 a_{m,s}（作为「外部选项」）。这是一个小参数、可解释的基线，
适合样本极少的在线更新；后续可升级为贝叶斯/MNL。

特征变换：transforms 支持 "log"（对数变换，对应广告/研发的边际收益递减，
避免线性模型在优化时退化为角落解）。注意：线性特征在优化时会产生
「要么最大、要么最小」的角落解，真实市场存在饱和效应，优化时应尽量
对广告/渠道/研发使用 log 变换。

估计用 numpy 最小二乘（对数几率回归），避免引入 sklearn 依赖。
"""
from __future__ import annotations

from math import exp, log

import numpy as np

from ..schemas import DecisionVector, TurnRecord
from .base import DemandEstimator, DemandModel

_EPS = 1e-9


def _logit(share: float) -> float:
    return log(max(share, _EPS) / (1.0 - max(share, _EPS)))


class LogitDemandModel(DemandModel):
    """logit 模型：细分截距 + 共享特征弹性。"""

    def __init__(
        self,
        segment_intercepts: dict[tuple[str, str], float],
        feature_betas: dict[str, float],
        transforms: dict[str, str] | None = None,
    ) -> None:
        self.segment_intercepts = dict(segment_intercepts)
        self.feature_betas = dict(feature_betas)
        self.transforms = dict(transforms or {})

    def _feature_value(self, name: str, decision: DecisionVector) -> float:
        x = decision.get(name)
        if self.transforms.get(name) == "log":
            return log(max(x, _EPS))
        return x

    def predict_logit(self, decision: DecisionVector, market: str, segment: str) -> float:
        z = self.segment_intercepts.get((market, segment), 0.0)
        for name, beta in self.feature_betas.items():
            z += beta * self._feature_value(name, decision)
        return z

    def predict_share(self, decision: DecisionVector, market: str, segment: str) -> float:
        z = self.predict_logit(decision, market, segment)
        # 数值稳定裁剪
        if z > 50.0:
            return 1.0
        if z < -50.0:
            return 0.0
        return 1.0 / (1.0 + exp(-z))


class LogitDemandEstimator(DemandEstimator):
    """对数几率回归估计 logit 需求模型。

    特征弹性跨细分共享（借用强度），细分截距独立（捕捉对手聚合强度差异）。
    transforms 与 LogitDemandModel 一致：{"log"} 表示对数变换。
    """

    def __init__(self, features: list[str], transforms: dict[str, str] | None = None) -> None:
        self.features = list(features)
        self.transforms = dict(transforms or {})

    def _transform(self, name: str, value: float) -> float:
        if self.transforms.get(name) == "log":
            return log(max(value, _EPS))
        return value

    def fit(self, records: list[TurnRecord]) -> LogitDemandModel:
        rows: list[tuple[str, str, list[float], float]] = []
        for r in records:
            om = r.outcome_map()
            for (market, segment), o in om.items():
                if not (0.0 < o.our_share < 1.0):
                    continue
                x = [self._transform(f, r.decision.get(f)) for f in self.features]
                rows.append((market, segment, x, _logit(o.our_share)))

        if not rows:
            raise ValueError("没有可用观测：需要 share 落在 (0,1) 开区间内的细分结果")

        seg_keys = sorted({(m, s) for m, s, _, _ in rows})
        seg_index = {key: i for i, key in enumerate(seg_keys)}
        n = len(rows)
        k = len(self.features)
        p = len(seg_keys) + k
        x_mat = np.zeros((n, p))
        y_vec = np.zeros(n)
        for i, (m, s, x, y) in enumerate(rows):
            x_mat[i, seg_index[(m, s)]] = 1.0
            if k:
                x_mat[i, len(seg_keys):] = x
            y_vec[i] = y

        coef, *_ = np.linalg.lstsq(x_mat, y_vec, rcond=None)
        segment_intercepts = {key: float(coef[seg_index[key]]) for key in seg_keys}
        feature_betas = {f: float(coef[len(seg_keys) + j]) for j, f in enumerate(self.features)}
        return LogitDemandModel(segment_intercepts, feature_betas, transforms=self.transforms)
