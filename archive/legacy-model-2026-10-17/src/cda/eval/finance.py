"""财务仿真：损益表 + 亏损结转 + 税。

依据决策指南 §8.1 损益表结构：
  总收入 = 产品销售收入 + 维修收入
  毛利润 = 总收入 − 可变成本
  营业利润 = 毛利润 − 固定成本（管理/广告/渠道/市场调研/生产线/研发等）
  税前利润 = 营业利润 + 利息收入 − 利息支出
  净利润 = 税前利润 − 税；亏损结转：前几回合亏损可抵未来税。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IncomeStatement:
    revenue: float = 0.0
    service_revenue: float = 0.0
    variable_cost: float = 0.0
    fixed_cost: float = 0.0
    interest_income: float = 0.0
    interest_expense: float = 0.0
    tax_rate: float = 0.25

    @property
    def gross_profit(self) -> float:
        return self.revenue + self.service_revenue - self.variable_cost

    @property
    def operating_profit(self) -> float:
        return self.gross_profit - self.fixed_cost

    @property
    def pretax_profit(self) -> float:
        return self.operating_profit + self.interest_income - self.interest_expense


@dataclass
class TaxTracker:
    """亏损结转：累计未弥补亏损，抵减未来税前利润后再计税。"""

    carryforward: float = 0.0  # 正值 = 可抵扣的累计亏损
    tax_rate: float = 0.25

    def net_profit(self, pretax: float) -> float:
        taxable = max(0.0, pretax - self.carryforward)
        tax = taxable * self.tax_rate
        net = pretax - tax
        # 更新结转：本回合若亏损，增加可抵扣亏损；若盈利，已抵扣部分减少结转
        if pretax < 0:
            self.carryforward += -pretax
        else:
            self.carryforward = max(0.0, self.carryforward - max(0.0, pretax))
        return net
