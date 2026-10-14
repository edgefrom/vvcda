"""统一数据结构的基础测试。"""
from __future__ import annotations

from cda.schemas import DecisionField, DecisionSchema, DecisionVector


def test_bounds_excludes_categorical() -> None:
    schema = DecisionSchema(
        fields={
            "price": DecisionField(name="price", kind="continuous", lower=0, upper=100),
            "qty": DecisionField(name="qty", kind="integer", lower=0, upper=50),
            "style": DecisionField(name="style", kind="categorical"),
        }
    )
    bounds = schema.bounds()
    assert set(bounds) == {"price", "qty"}
    assert bounds["price"] == (0.0, 100.0)
    assert schema.integer_fields() == ["qty"]
    assert schema.continuous_fields() == ["price", "qty"]


def test_decision_vector_get_default() -> None:
    d = DecisionVector(turn=1, values={"price": 399.0})
    assert d.get("price") == 399.0
    assert d.get("missing") == 0.0
    assert d.get("missing", -1.0) == -1.0


def test_decision_field_applies_to_default_empty() -> None:
    f = DecisionField(name="ad")
    assert f.applies_to == ()
    assert f.kind == "continuous"
