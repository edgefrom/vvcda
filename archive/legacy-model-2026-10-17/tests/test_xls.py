"""结果导出 xls 解析器测试（用真实练习回合数据）。"""
from __future__ import annotations

import os

import pytest

from cda.adapters.xls_source import parse_results
from cda.schemas import MarketResult

XLS = os.path.join("data", "raw", "results", "results-pr01.xls")


@pytest.mark.skipif(not os.path.exists(XLS), reason="缺少练习回合结果文件")
def test_parse_results_structure() -> None:
    result = parse_results(XLS)
    assert isinstance(result, MarketResult)
    assert len(result.companies) == 10  # 本赛区 10 支队伍
    names = [c.company for c in result.companies]
    assert len(set(names)) == len(names)  # 队名唯一


@pytest.mark.skipif(not os.path.exists(XLS), reason="缺少练习回合结果文件")
def test_parse_results_values() -> None:
    result = parse_results(XLS)
    first = result.companies[0]
    # 每队 8 个细分份额（2 市场 × 4 细分）
    assert len(first.shares) == 8
    # 股价为浮点
    assert first.stock_price is not None and first.stock_price > 0
    # 对手可见
    assert len(result.opponents(first.company)) == 9


@pytest.mark.skipif(not os.path.exists(XLS), reason="缺少练习回合结果文件")
def test_parse_results_every_company_has_data() -> None:
    result = parse_results(XLS)
    for c in result.companies:
        assert c.shares, f"{c.company} 无份额数据"
        assert c.stock_price is not None
