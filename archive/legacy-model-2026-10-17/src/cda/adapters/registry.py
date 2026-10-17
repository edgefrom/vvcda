"""数据源注册表：按名字获取适配器实现，便于扩展多接口。"""
from __future__ import annotations

from typing import Callable, TypeVar

from ..schemas import DecisionSchema
from .base import DataSource
from .csv_source import CsvDataSource
from .json_source import JsonDataSource
from .memory_source import MemoryDataSource

# 工厂签名：接收 schema 与任意关键字参数，返回 DataSource
Factory = Callable[..., DataSource]
T = TypeVar("T", bound=DataSource)

SOURCES: dict[str, Factory] = {
    "json": lambda schema=None, **kw: JsonDataSource(schema=schema, **kw),
    "csv": lambda schema=None, **kw: CsvDataSource(schema=schema, **kw),
    "memory": lambda schema=None, **kw: MemoryDataSource(schema=schema, **kw),
}


def register_source(name: str, factory: Factory) -> None:
    """注册新的数据源工厂。"""
    SOURCES[name] = factory


def get_source(name: str, schema: DecisionSchema | None = None, **kwargs: object) -> DataSource:
    """按名字实例化数据源。未知名抛出 KeyError。"""
    if name not in SOURCES:
        raise KeyError(f"未知数据源: {name!r}，可用: {sorted(SOURCES)}")
    return SOURCES[name](schema=schema, **kwargs)
