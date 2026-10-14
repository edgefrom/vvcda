"""相对特征工程：把结果快照转成需求模型的相对特征。

依据决策指南 §2.2.2：市场份额取决于
  相对价格、相对广告、相对渠道投资、产品属性、客户服务。

本模块把 CompanyResult（含全市场信息）转成这些相对量，
并支持直接拟合一个「相对份额模型」。
"""
from __future__ import annotations

from math import log

import numpy as np

from ..schemas import CompanyResult, MarketResult, SEGMENTS_DEFAULT

SEGMENTS = list(SEGMENTS_DEFAULT)
FEATURES = ["高像素", "额外存储", "高级屏幕", "导航功能", "安全功能"]


def _avg(values: list[float]) -> float:
    vals = [v for v in values if v and v > 0]
    return sum(vals) / len(vals) if vals else 0.0


def company_average_price(c: CompanyResult, market: str) -> float:
    prices = [v for k, v in c.prices.items() if k.startswith(market + ":") and v > 0]
    return sum(prices) / len(prices) if prices else 0.0


def relative_features(c: CompanyResult, market_result: MarketResult, market: str) -> dict[str, float]:
    """计算一家公司在一个市场的相对特征。"""
    avg_prices = [company_average_price(x, market) for x in market_result.companies]
    mkt_price = _avg(avg_prices)
    rel_price = (company_average_price(c, market) / mkt_price) if mkt_price else 1.0

    ads = [x.advertising.get(market, 0.0) for x in market_result.companies]
    mkt_ad = _avg(ads)
    rel_ad = (c.advertising.get(market, 0.0) / mkt_ad) if mkt_ad else 1.0

    chans = [x.channel_investment.get(market, 0.0) for x in market_result.companies]
    mkt_chan = _avg(chans)
    rel_channel = (c.channel_investment.get(market, 0.0) / mkt_chan) if mkt_chan else 1.0

    attrs = [a for k, a in c.product_attributes.items() if k.startswith(market + ":")]
    thinness = _avg([a.get("thinness", 0.0) for a in attrs])
    battery = _avg([a.get("battery", 0.0) for a in attrs])
    n_features = _avg([sum(1 for f in FEATURES if a.get(f, 0.0) > 0) for a in attrs])

    return {
        "rel_price": rel_price,
        "rel_ad": rel_ad,
        "rel_channel": rel_channel,
        "thinness": thinness,
        "battery": battery,
        "n_features": n_features,
    }


def build_dataset(
    market_result: MarketResult, market: str, feature_names: list[str]
) -> tuple[np.ndarray, np.ndarray, list[tuple[str, str]]]:
    """从全市场快照构建 (X, y, keys)，y 为 logit(份额)。份额在 (0,100) 内才纳入。"""
    rows: list[list[float]] = []
    ys: list[float] = []
    keys: list[tuple[str, str]] = []
    for c in market_result.companies:
        feats = relative_features(c, market_result, market)
        x = [feats[n] for n in feature_names]
        for seg in SEGMENTS:
            share = c.shares.get(f"{market}:{seg}", 0.0)
            if 0.0 < share < 100.0:
                rows.append(x)
                ys.append(log(share / (100.0 - share)))
                keys.append((c.company, seg))
    return np.asarray(rows, dtype=float), np.asarray(ys, dtype=float), keys


def fit_relative_model(
    market_result: MarketResult, market: str, feature_names: list[str], fit_intercept: bool = True
) -> dict[str, float]:
    """用最小二乘拟合 logit(份额) = 截距 + Σ β · 相对特征，返回 {特征: 系数}。

    fit_intercept=True 时返回额外的 "intercept" 键（各细分基准份额的基线）。
    """
    x, y, _ = build_dataset(market_result, market, feature_names)
    if x.shape[0] == 0:
        return {n: 0.0 for n in feature_names}
    if fit_intercept:
        x = np.column_stack([np.ones(x.shape[0]), x])
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    if fit_intercept:
        return {"intercept": float(coef[0]), **{n: float(coef[i + 1]) for i, n in enumerate(feature_names)}}
    return {n: float(coef[i]) for i, n in enumerate(feature_names)}
