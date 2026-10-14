"""非线性诊断测试。"""
from __future__ import annotations

import numpy as np

from cda.demand.diagnostics import diagnostics, is_linear_sufficient
from cda.schemas import CompanyResult, MarketResult

SEGMENTS = ["consumer", "premium", "business", "premium_business"]


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + np.exp(-z))


def _make_market(prices: list[float]) -> MarketResult:
    companies = []
    for i, p in enumerate(prices):
        share = _sigmoid(-0.02 * (p - 350.0))
        companies.append(
            CompanyResult(
                company=f"C{i}",
                turn=0,
                prices={"EU:P1": p},
                advertising={"EU": 100.0},
                channel_investment={"EU": 50.0},
                shares={f"EU:{seg}": share * 100.0 for seg in SEGMENTS},
                product_attributes={"EU:P1": {"thinness": 100.0, "battery": 100.0, "高像素": 1, "额外存储": 1, "高级屏幕": 1, "导航功能": 1, "安全功能": 1}},
            )
        )
    return MarketResult(turn=0, companies=companies)


def test_diagnostics_high_r2_on_clean_price_signal() -> None:
    market = _make_market([250.0, 300.0, 350.0, 400.0, 450.0, 500.0])
    diag = diagnostics(market, "EU", ["rel_price"])
    assert diag["n"] == 24
    assert diag["r2"] > 0.9
    assert is_linear_sufficient(diag)


def test_diagnostics_reports_nan_on_tiny_data() -> None:
    market = _make_market([300.0, 350.0])
    diag = diagnostics(market, "EU", ["rel_price"])
    assert diag["n"] == 8
    # 少量数据也应返回数值字段
    assert "r2" in diag
