"""数据适配层：把外部数据形态转成统一 TurnRecord。

真实平台的数据通过人工录入/手动导出后，由本层各实现类适配。
"""
from __future__ import annotations

from .base import DataSource
from .csv_source import CsvDataSource
from .json_source import JsonDataSource
from .memory_source import MemoryDataSource
from .registry import SOURCES, get_source, register_source
from .xls_source import XlsResultsSource, parse_results

__all__ = [
    "DataSource",
    "CsvDataSource",
    "JsonDataSource",
    "MemoryDataSource",
    "XlsResultsSource",
    "parse_results",
    "SOURCES",
    "get_source",
    "register_source",
]
