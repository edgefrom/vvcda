"""端到端演示：合成数据 → 需求估计 → 蒙特卡洛评估 → 差分进化搜索 → 建议输出。

运行：python scripts/demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402

from cda.demand import LogitDemandEstimator, LogitDemandModel  # noqa: E402
from cda.eval import FinancialModel, ProxyObjective, evaluate_decision, make_scenarios  # noqa: E402
from cda.optimize import differential_evolution_search  # noqa: E402
from cda.output import Recommendation  # noqa: E402
from cda.schemas import DecisionVector, SegmentOutcome, TurnRecord  # noqa: E402

FEATURES = ["price_EU", "price_ASIA", "advertising_EU", "advertising_ASIA", "rd_investment"]
# 广告/研发用 log 变换（边际收益递减），避免优化退化为角落解
TRANSFORMS = {"advertising_EU": "log", "advertising_ASIA": "log", "rd_investment": "log"}
MARKETS_SEGMENTS = [
    ("EU", "consumer"), ("EU", "premium"), ("EU", "business"), ("EU", "premium_business"),
    ("ASIA", "consumer"), ("ASIA", "premium"), ("ASIA", "business"), ("ASIA", "premium_business"),
]


def synthetic_true_model() -> LogitDemandModel:
    intercepts = {ms: -1.0 - 0.3 * i for i, ms in enumerate(MARKETS_SEGMENTS)}
    betas = {
        "price_EU": -0.01, "price_ASIA": -0.01,
        "advertising_EU": 0.03, "advertising_ASIA": 0.03,
        "rd_investment": 0.02,
    }
    return LogitDemandModel(intercepts, betas, transforms=TRANSFORMS)


def generate_records(model: LogitDemandModel, n: int = 12, seed: int = 7) -> list[TurnRecord]:
    rng = np.random.default_rng(seed)
    records: list[TurnRecord] = []
    for t in range(n):
        d = DecisionVector(
            turn=t,
            values={
                "price_EU": float(rng.uniform(250, 500)),
                "price_ASIA": float(rng.uniform(250, 500)),
                "advertising_EU": float(rng.uniform(10, 200)),
                "advertising_ASIA": float(rng.uniform(10, 200)),
                "rd_investment": float(rng.uniform(10, 150)),
                "production_qty": 3000.0,
            },
        )
        outcomes = []
        for (m, s) in MARKETS_SEGMENTS:
            share = model.predict_share(d, m, s)
            z = np.log(share / (1 - share)) + rng.normal(0.0, 0.05)
            share_n = 1.0 / (1.0 + np.exp(-z))
            outcomes.append(SegmentOutcome(market=m, segment=s, our_share=share_n, our_sales=share_n * 1000.0, market_sales=1000.0))
        records.append(TurnRecord(turn=t, decision=d, outcomes=outcomes))
    return records


def main() -> None:
    true = synthetic_true_model()
    records = generate_records(true)
    estimator = LogitDemandEstimator(FEATURES, transforms=TRANSFORMS)
    model = estimator.fit(records)

    print("== 真实弹性 vs 估计弹性 ==")
    for f in FEATURES:
        print(f"  {f}: 真 {true.feature_betas[f]:+.4f} | 估 {model.feature_betas[f]:+.4f}")

    scenarios = make_scenarios(
        model,
        MARKETS_SEGMENTS,
        noise_std=0.1,
        n_scenarios=300,
        market_sizes={ms: 1000.0 for ms in MARKETS_SEGMENTS},
    )
    fin_model = FinancialModel(
        unit_cost=0.5,
        expense_fields=["advertising_EU", "advertising_ASIA", "rd_investment"],
    )
    objective = ProxyObjective()

    # 注意：边界应来自真实决策表单 schema（config/decision_schema.yaml）。
    # log 变换的字段下限取 1（log 需 >0）；价格下限避免在价格=0 处退化。
    bounds = {
        "price_EU": (50.0, 600.0),
        "price_ASIA": (50.0, 600.0),
        "advertising_EU": (1.0, 200.0),
        "advertising_ASIA": (1.0, 200.0),
        "rd_investment": (1.0, 150.0),
        "production_qty": (0.0, 8000.0),
    }

    def objective_fn(d: dict[str, float]) -> float:
        decision = DecisionVector(turn=0, values=d)
        return -evaluate_decision(decision, scenarios, fin_model, objective).mean

    result = differential_evolution_search(objective_fn, bounds, integer_fields=("production_qty",), maxiter=150)
    best = DecisionVector(turn=0, values=result.best)
    eval_res = evaluate_decision(best, scenarios, fin_model, objective)

    rec = Recommendation(
        turn=1,
        decision=best,
        rationale="在估计需求模型 + 蒙特卡洛情景下最大化代理目标（利润/份额/增长加权）。",
        confidence="low",
        risks=["需求参数仅由合成数据估计，真实数据接入后需重新校准；", "股价函数为黑箱，当前为代理目标。"],
    )
    print()
    print(rec.to_markdown())
    print()
    print("== 情景评估 ==")
    print(eval_res.summary())


if __name__ == "__main__":
    main()
