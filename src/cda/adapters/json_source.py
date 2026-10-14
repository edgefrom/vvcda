"""JSON 数据源：每回合一个 JSON 文件，完整往返。"""
from __future__ import annotations

import json
import os

from ..schemas import DecisionSchema, TurnRecord
from .base import DataSource
from .serialize import turn_from_dict, turn_to_dict


class JsonDataSource(DataSource):
    """目录下的 turn_NN.json 文件，每个文件是一条完整回合记录。"""

    def __init__(self, directory: str, schema: DecisionSchema | None = None, **kwargs: object) -> None:
        super().__init__(schema, **kwargs)
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path(self, turn: int) -> str:
        return os.path.join(self.directory, f"turn_{turn:02d}.json")

    def load_turns(self) -> list[TurnRecord]:
        records: list[TurnRecord] = []
        if not os.path.isdir(self.directory):
            return records
        for name in sorted(os.listdir(self.directory)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(self.directory, name), encoding="utf-8") as fh:
                records.append(turn_from_dict(json.load(fh)))
        records.sort(key=lambda r: r.turn)
        return records

    def save_turn(self, record: TurnRecord) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(record.turn), "w", encoding="utf-8") as fh:
            json.dump(turn_to_dict(record), fh, ensure_ascii=False, indent=2)
