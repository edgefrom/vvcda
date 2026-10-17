"""数据源往返读写测试。"""
from __future__ import annotations

from cda.adapters import CsvDataSource, JsonDataSource, MemoryDataSource
from cda.schemas import DecisionField, DecisionSchema, DecisionVector, Financials, SegmentOutcome, TurnRecord


def _schema() -> DecisionSchema:
    return DecisionSchema(
        fields={
            "price": DecisionField(name="price", kind="continuous", lower=0, upper=1000),
            "advertising": DecisionField(name="advertising", kind="continuous", lower=0, upper=500),
        }
    )


def _record(turn: int) -> TurnRecord:
    return TurnRecord(
        turn=turn,
        decision=DecisionVector(turn=turn, values={"price": 399.0 + turn, "advertising": 100.0}, notes="测试"),
        outcomes=[SegmentOutcome(market="EU", segment="consumer", our_share=0.12, our_sales=1200.0, market_sales=10000.0)],
        financials=Financials(revenue=478800.0, cost=350000.0, profit=128800.0, cash=800000.0),
        stock_price=12.5,
    )


def test_memory_roundtrip() -> None:
    src = MemoryDataSource()
    src.save_turn(_record(1))
    src.save_turn(_record(2))
    turns = src.load_turns()
    assert [t.turn for t in turns] == [1, 2]
    assert turns[0].decision.values["price"] == 400.0
    assert turns[0].outcomes[0].our_share == 0.12


def test_json_roundtrip(tmp_path) -> None:
    src = JsonDataSource(directory=str(tmp_path / "turns"))
    src.save_turn(_record(1))
    src.save_turn(_record(2))
    turns = src.load_turns()
    assert [t.turn for t in turns] == [1, 2]
    assert turns[0].financials.profit == 128800.0
    assert turns[0].stock_price == 12.5
    assert turns[0].outcomes[0].our_sales == 1200.0


def test_csv_roundtrip(tmp_path) -> None:
    src = CsvDataSource(path=str(tmp_path / "turns.csv"), schema=_schema())
    src.save_turn(_record(1))
    turns = src.load_turns()
    assert len(turns) == 1
    assert turns[0].decision.values["price"] == 400.0
    assert turns[0].financials.profit == 128800.0
