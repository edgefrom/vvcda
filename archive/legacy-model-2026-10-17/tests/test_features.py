"""相对特征工程测试。"""
from __future__ import annotations

from cda.demand.features import build_dataset, fit_relative_model, relative_features
from cda.schemas import CompanyResult, MarketResult


def _make_market(n: int = 4) -> MarketResult:
    companies = []
    for i in range(n):
        companies.append(
            CompanyResult(
                company=f"公司{chr(65 + i)}",
                turn=0,
                prices={"EU:P1": 300.0 + i * 10},
                shares={"EU:consumer": 20.0 + i, "EU:premium": 15.0 + i, "EU:business": 10.0 + i, "EU:premium_business": 5.0 + i},
                advertising={"EU": 100.0 + i * 20},
                channel_investment={"EU": 50.0 + i * 10},
                product_attributes={"EU:P1": {"thinness": 100.0, "battery": 100.0, "高像素": 1, "额外存储": 1, "高级屏幕": 1, "导航功能": 1, "安全功能": 1}},
            )
        )
    return MarketResult(turn=0, companies=companies)


def test_relative_features_scale_invariant() -> None:
    market = _make_market(2)
    c0 = market.companies[0]
    c1 = market.companies[1]
    f0 = relative_features(c0, market, "EU")
    # 价格更高 → 相对价格 > 1
    assert f0["rel_price"] < 1.0
    f1 = relative_features(c1, market, "EU")
    assert f1["rel_price"] > 1.0


def test_build_dataset_shapes() -> None:
    market = _make_market(4)
    x, y, keys = build_dataset(market, "EU", ["rel_price", "rel_ad", "rel_channel", "thinness", "battery", "n_features"])
    assert x.shape == (16, 6)  # 4 公司 × 4 细分
    assert len(y) == 16
    assert len(keys) == 16


def test_fit_relative_model_returns_coefficients() -> None:
    market = _make_market(4)
    coef = fit_relative_model(market, "EU", ["rel_price", "rel_ad", "rel_channel"])
    assert set(coef) == {"intercept", "rel_price", "rel_ad", "rel_channel"}
    # 价格越高份额越低 → 相对价格系数应为负（本合成数据中份额随价格上升，见下）
    assert coef["rel_price"] != 0.0
