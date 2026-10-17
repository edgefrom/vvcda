"""决策约束：从 schema 生成边界，以及通用预算约束检查。"""
from __future__ import annotations

from ..schemas import DecisionSchema, DecisionVector


def bounds_from_schema(schema: DecisionSchema) -> dict[str, tuple[float, float]]:
    """返回连续/整数字段的 (lower, upper) 边界，供搜索器使用。"""
    return schema.bounds()


def budget_violations(
    decision: DecisionVector,
    budget: float,
    cost_per_unit: dict[str, float],
) -> list[str]:
    """检查简单预算约束：Σ 成本字段 × 取值 ≤ budget。

    返回违反说明列表（空列表表示满足）。这是先验模板；真实预算/贷款约束
    登录平台确认后，替换为更精确的实现。
    """
    total = 0.0
    for field, unit_cost in cost_per_unit.items():
        total += decision.get(field) * unit_cost
    if total > budget:
        return [f"预算超支：{total:.2f} > {budget:.2f}"]
    return []
