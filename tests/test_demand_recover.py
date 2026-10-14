"""合成数据测试：已知参数生成需求 → 估计脚本恢复参数。"""
from __future__ import annotations

import numpy as np

from cda.demand import LogitDemandEstimator, LogitDemandModel
from cda.schemas import DecisionVector, SegmentOutcome, TurnRecord

FEATURES = ["price", "advertising"]


def _true_model() -> LogitDemandModel:
    intercepts = {
        ("EU", "consumer"): -1.0,
        ("EU", "premium"): -0.5,
        ("ASIA", "consumer"): -0.8,
        ("ASIA", "premium"): -0.2,
    }
    betas = {"price": -0.01, "advertising": 0.005}
    return LogitDemandModel(intercepts, betas)


def _generate(model: LogitDemandModel, n: int = 60, seed: int = 0) -> list[TurnRecord]:
    rng = np.random.default_rng(seed)
    records: list[TurnRecord] = []
    for t in range(n):
        d = DecisionVector(
            turn=t,
            values={"price": float(rng.uniform(200, 600)), "advertising": float(rng.uniform(0, 200))},
        )
        outcomes: list[SegmentOutcome] = []
        for (m, s) in model.segment_intercepts:
            share = model.predict_share(d, m, s)
            z = np.log(share / (1 - share)) + rng.normal(0.0, 0.05)
            share_noisy = 1.0 / (1.0 + np.exp(-z))
            outcomes.append(
                SegmentOutcome(market=m, segment=s, our_share=share_noisy, our_sales=share_noisy * 1000.0, market_sales=1000.0)
            )
        records.append(TurnRecord(turn=t, decision=d, outcomes=outcomes))
    return records


def test_recover_feature_betas() -> None:
    true = _true_model()
    est = LogitDemandEstimator(FEATURES).fit(_generate(true))
    for f in FEATURES:
        assert abs(est.feature_betas[f] - true.feature_betas[f]) < 0.002, (
            f"字段 {f} 恢复失败：{est.feature_betas[f]} vs {true.feature_betas[f]}"
        )


def test_recover_intercepts_loosely() -> None:
    true = _true_model()
    est = LogitDemandEstimator(FEATURES).fit(_generate(true))
    for key in true.segment_intercepts:
        assert abs(est.segment_intercepts[key] - true.segment_intercepts[key]) < 0.3


def test_recover_betas_with_log_transform() -> None:
    intercepts = {("EU", "consumer"): -1.0, ("EU", "premium"): -0.5}
    transforms = {"advertising": "log"}
    true = LogitDemandModel(intercepts, {"price": -0.01, "advertising": 0.4}, transforms=transforms)
    rng = np.random.default_rng(1)
    records: list[TurnRecord] = []
    for t in range(80):
        d = DecisionVector(
            turn=t,
            values={"price": float(rng.uniform(200, 600)), "advertising": float(rng.uniform(10, 200))},
        )
        outcomes: list[SegmentOutcome] = []
        for (m, s) in intercepts:
            share = true.predict_share(d, m, s)
            z = np.log(share / (1 - share)) + rng.normal(0.0, 0.05)
            share_n = 1.0 / (1.0 + np.exp(-z))
            outcomes.append(SegmentOutcome(market=m, segment=s, our_share=share_n, our_sales=share_n * 1000.0, market_sales=1000.0))
        records.append(TurnRecord(turn=t, decision=d, outcomes=outcomes))
    est = LogitDemandEstimator(["price", "advertising"], transforms=transforms).fit(records)
    assert abs(est.feature_betas["advertising"] - 0.4) < 0.03
    assert abs(est.feature_betas["price"] + 0.01) < 0.002


def test_raises_without_usable_observations() -> None:
    import pytest

    records = [
        TurnRecord(
            turn=0,
            decision=DecisionVector(turn=0, values={"price": 1.0, "advertising": 1.0}),
            outcomes=[SegmentOutcome(market="EU", segment="consumer", our_share=0.0)],
        )
    ]
    with pytest.raises(ValueError):
        LogitDemandEstimator(FEATURES).fit(records)
