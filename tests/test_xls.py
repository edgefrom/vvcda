"""结果导出 xls 解析器测试（用真实文件）。"""
from __future__ import annotations

import os

import pytest

from cda.adapters.xls_source import parse_results
from cda.schemas import MarketResult

XLS = os.path.join("manual_download", "results-ir00.xls")


@pytest.mark.skipif(not os.path.exists(XLS), reason="缺少 results-ir00.xls")
def test_parse_results_structure() -> None:
    result = parse_results(XLS)
    assert isinstance(result, MarketResult)
    assert len(result.companies) == 12
    names = [c.company for c in result.companies]
    assert names[0].startswith("公司")
    assert len(set(names)) == 12


@pytest.mark.skipif(not os.path.exists(XLS), reason="缺少 results-ir00.xls")
def test_parse_results_values() -> None:
    result = parse_results(XLS)
    a = result.company("公司A")
    assert a is not None
    # 定价（市场区：每公司 6 产品列）
    assert a.prices.get("EU:P1") == pytest.approx(399.0)
    # 研发（财务区：每公司 1 列）
    assert a.rd_investment == pytest.approx(6500.0)
    # 对手可见
    assert len(result.opponents("公司A")) == 11
    # 股价为浮点
    assert a.stock_price is not None and a.stock_price > 0


@pytest.mark.skipif(not os.path.exists(XLS), reason="缺少 results-ir00.xls")
def test_parse_results_every_company_has_data() -> None:
    result = parse_results(XLS)
    for c in result.companies:
        assert c.prices, f"{c.company} 无定价数据"
        assert c.shares, f"{c.company} 无份额数据"
        assert c.stock_price is not None
