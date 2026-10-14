"""核心对象的显式序列化（用于 JSON 往返）。"""
from __future__ import annotations

from typing import Any

from ..schemas import (
    DecisionVector,
    Financials,
    SegmentOutcome,
    TurnRecord,
)


def decision_to_dict(d: DecisionVector) -> dict[str, Any]:
    return {"turn": d.turn, "values": dict(d.values), "notes": d.notes}


def decision_from_dict(data: dict[str, Any]) -> DecisionVector:
    return DecisionVector(
        turn=int(data.get("turn", 0)),
        values={str(k): float(v) for k, v in data.get("values", {}).items()},
        notes=str(data.get("notes", "")),
    )


def outcome_to_dict(o: SegmentOutcome) -> dict[str, Any]:
    return {
        "market": o.market,
        "segment": o.segment,
        "our_sales": o.our_sales,
        "market_sales": o.market_sales,
        "our_share": o.our_share,
    }


def outcome_from_dict(data: dict[str, Any]) -> SegmentOutcome:
    return SegmentOutcome(
        market=str(data.get("market", "")),
        segment=str(data.get("segment", "")),
        our_sales=float(data.get("our_sales", 0.0)),
        market_sales=float(data.get("market_sales", 0.0)),
        our_share=float(data.get("our_share", 0.0)),
    )


def financials_to_dict(f: Financials | None) -> dict[str, Any] | None:
    if f is None:
        return None
    return {
        "revenue": f.revenue,
        "cost": f.cost,
        "profit": f.profit,
        "cash": f.cash,
        "inventory": f.inventory,
        "extra": dict(f.extra),
    }


def financials_from_dict(data: dict[str, Any] | None) -> Financials | None:
    if data is None:
        return None
    return Financials(
        revenue=float(data.get("revenue", 0.0)),
        cost=float(data.get("cost", 0.0)),
        profit=float(data.get("profit", 0.0)),
        cash=float(data.get("cash", 0.0)),
        inventory=float(data.get("inventory", 0.0)),
        extra={str(k): float(v) for k, v in data.get("extra", {}).items()},
    )


def turn_to_dict(r: TurnRecord) -> dict[str, Any]:
    return {
        "turn": r.turn,
        "decision": decision_to_dict(r.decision),
        "outcomes": [outcome_to_dict(o) for o in r.outcomes],
        "financials": financials_to_dict(r.financials),
        "stock_price": r.stock_price,
        "extra": r.extra,
    }


def turn_from_dict(data: dict[str, Any]) -> TurnRecord:
    return TurnRecord(
        turn=int(data.get("turn", 0)),
        decision=decision_from_dict(data.get("decision", {})),
        outcomes=[outcome_from_dict(o) for o in data.get("outcomes", [])],
        financials=financials_from_dict(data.get("financials")),
        stock_price=data.get("stock_price"),
        extra=data.get("extra", {}),
    )
