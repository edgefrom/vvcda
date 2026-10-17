"""CSV 数据源：Excel 友好的决策日志（扁平化，不含细分明细）。

注意：CSV 只保存决策 + 财务汇总 + 股价，用于人类快速浏览/Excel 分析。
细分销量/份额的完整明细请用 JsonDataSource。
"""
from __future__ import annotations

import csv
import os

from ..schemas import DecisionSchema, DecisionVector, Financials, TurnRecord
from .base import DataSource

_COLUMNS = [
    "turn",
    "revenue",
    "cost",
    "profit",
    "cash",
    "inventory",
    "stock_price",
    "notes",
]


class CsvDataSource(DataSource):
    """单文件 CSV：data/turns.csv，列 = turn + 决策字段 + 财务汇总 + 股价。"""

    def __init__(self, path: str, schema: DecisionSchema | None = None, **kwargs: object) -> None:
        super().__init__(schema, **kwargs)
        self.path = path

    def _fieldnames(self, schema: DecisionSchema | None) -> list[str]:
        decision_cols = schema.field_names() if schema is not None else []
        return ["turn", *decision_cols, *_COLUMNS[1:]]

    def load_turns(self) -> list[TurnRecord]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            records: list[TurnRecord] = []
            for row in reader:
                decision_cols = (
                    self.schema.field_names() if self.schema is not None else
                    [c for c in row if c not in _COLUMNS]
                )
                values = {
                    c: float(row.get(c) or 0.0)
                    for c in decision_cols
                    if c in row and row.get(c) not in (None, "")
                }
                fin = Financials(
                    revenue=float(row.get("revenue") or 0.0),
                    cost=float(row.get("cost") or 0.0),
                    profit=float(row.get("profit") or 0.0),
                    cash=float(row.get("cash") or 0.0),
                    inventory=float(row.get("inventory") or 0.0),
                )
                records.append(
                    TurnRecord(
                        turn=int(row.get("turn") or 0),
                        decision=DecisionVector(turn=int(row.get("turn") or 0), values=values, notes=row.get("notes", "")),
                        financials=fin,
                        stock_price=float(row["stock_price"]) if row.get("stock_price") not in (None, "") else None,
                    )
                )
            records.sort(key=lambda r: r.turn)
            return records

    def save_turn(self, record: TurnRecord) -> None:
        rows = self.load_turns()
        by_turn = {r.turn: r for r in rows}
        by_turn[record.turn] = record
        all_rows = sorted(by_turn.values(), key=lambda r: r.turn)

        fieldnames = self._fieldnames(self.schema)
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in all_rows:
                row: dict[str, object] = {"turn": r.turn}
                row.update(r.decision.values)
                if r.financials is not None:
                    row.update(
                        {
                            "revenue": r.financials.revenue,
                            "cost": r.financials.cost,
                            "profit": r.financials.profit,
                            "cash": r.financials.cash,
                            "inventory": r.financials.inventory,
                        }
                    )
                row["stock_price"] = r.stock_price if r.stock_price is not None else ""
                row["notes"] = r.decision.notes
                writer.writerow(row)
