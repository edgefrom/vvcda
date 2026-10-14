"""搜索器收敛测试：差分进化应在合成目标上找到最小值。"""
from __future__ import annotations

from cda.optimize import differential_evolution_search


def test_de_finds_quadratic_minimum() -> None:
    def objective(d: dict[str, float]) -> float:
        return (d["x"] - 3.0) ** 2 + (d["y"] + 2.0) ** 2

    result = differential_evolution_search(
        objective,
        bounds={"x": (-10.0, 10.0), "y": (-10.0, 10.0)},
        seed=0,
        maxiter=500,
        popsize=15,
    )
    assert result.objective < 1e-4
    assert abs(result.best["x"] - 3.0) < 0.01
    assert abs(result.best["y"] + 2.0) < 0.01


def test_de_respects_integer_fields() -> None:
    def objective(d: dict[str, float]) -> float:
        return (d["qty"] - 7.4) ** 2

    result = differential_evolution_search(
        objective,
        bounds={"qty": (0.0, 20.0)},
        integer_fields=("qty",),
        seed=0,
        maxiter=300,
    )
    assert float(result.best["qty"]).is_integer()
