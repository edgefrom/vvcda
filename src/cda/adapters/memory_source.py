"""内存数据源：测试与 UI 会话使用。"""
from __future__ import annotations

from ..schemas import DecisionSchema, TurnRecord
from .base import DataSource


class MemoryDataSource(DataSource):
    def __init__(self, schema: DecisionSchema | None = None, **kwargs: object) -> None:
        super().__init__(schema, **kwargs)
        self._turns: dict[int, TurnRecord] = {}

    def load_turns(self) -> list[TurnRecord]:
        return [self._turns[t] for t in sorted(self._turns)]

    def save_turn(self, record: TurnRecord) -> None:
        self._turns[record.turn] = record
