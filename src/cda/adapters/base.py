"""数据源抽象接口。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas import DecisionSchema, TurnRecord


class DataSource(ABC):
    """统一数据源接口。真实平台适配器实现此接口。

    约定：
    - load_turns() 返回按回合号升序的历史记录。
    - save_turn() 对同回合号重复写入时覆盖。
    """

    def __init__(self, schema: DecisionSchema | None = None, **kwargs: object) -> None:
        self.schema = schema

    @abstractmethod
    def load_turns(self) -> list[TurnRecord]:
        """读取历史回合记录。"""

    @abstractmethod
    def save_turn(self, record: TurnRecord) -> None:
        """写入一条回合记录。"""

    def load_schema(self) -> DecisionSchema | None:
        """如果数据源能提供 schema，则返回；否则 None。"""
        return self.schema
