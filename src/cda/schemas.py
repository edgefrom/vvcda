"""统一数据结构：平台无关的经营状态、决策、结果、建议等核心对象。

本模块是全项目的依赖根：所有适配器、模型、优化器、评估与输出层
都围绕这些结构工作。真实平台字段名只出现在 config/*.yaml 与适配层，
核心结构不随平台变化。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# 默认市场与细分（可由 config 覆盖）
MARKETS_DEFAULT: tuple[str, ...] = ("EU", "ASIA")
SEGMENTS_DEFAULT: tuple[str, ...] = ("consumer", "premium", "business", "premium_business")


@dataclass(frozen=True)
class DecisionField:
    """单个决策字段的元信息（来自 config/decision_schema.yaml）。"""

    name: str
    unit: str = ""
    kind: str = "continuous"  # continuous | integer | categorical
    lower: float | None = None
    upper: float | None = None
    default: float | None = None
    applies_to: tuple[str, ...] = ()  # 作用于哪些市场；空 = 全局


@dataclass
class DecisionSchema:
    """决策表单的结构定义（平台相关，由 config 驱动）。"""

    fields: dict[str, DecisionField]
    markets: tuple[str, ...] = MARKETS_DEFAULT
    segments: tuple[str, ...] = SEGMENTS_DEFAULT

    def field_names(self) -> list[str]:
        return list(self.fields)

    def bounds(self) -> dict[str, tuple[float, float]]:
        """返回连续/整数字段的 (lower, upper) 边界。categorical 字段跳过。"""
        out: dict[str, tuple[float, float]] = {}
        for f in self.fields.values():
            if f.kind == "categorical":
                continue
            lo = f.lower if f.lower is not None else 0.0
            hi = f.upper if f.upper is not None else lo + 1.0
            out[f.name] = (lo, hi)
        return out

    def continuous_fields(self) -> list[str]:
        return [f.name for f in self.fields.values() if f.kind != "categorical"]

    def integer_fields(self) -> list[str]:
        return [f.name for f in self.fields.values() if f.kind == "integer"]


@dataclass
class DecisionVector:
    """一个回合的决策：字段名 -> 数值。"""

    turn: int
    values: dict[str, float]
    notes: str = ""

    def get(self, name: str, default: float = 0.0) -> float:
        return self.values.get(name, default)


@dataclass
class SegmentOutcome:
    """单个细分市场的结算结果。"""

    market: str
    segment: str
    our_sales: float = 0.0  # 我方销量
    market_sales: float = 0.0  # 该细分总销量
    our_share: float = 0.0  # 我方份额 [0,1]

    @property
    def key(self) -> tuple[str, str]:
        return (self.market, self.segment)


@dataclass
class Financials:
    """财务结果。未知字段放 extra，保证可迁移。"""

    revenue: float = 0.0
    cost: float = 0.0
    profit: float = 0.0
    cash: float = 0.0
    inventory: float = 0.0
    extra: dict[str, float] = field(default_factory=dict)


@dataclass
class TurnRecord:
    """一个回合的完整记录：决策 + 结果。"""

    turn: int
    decision: DecisionVector
    outcomes: list[SegmentOutcome] = field(default_factory=list)
    financials: Financials | None = None
    stock_price: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def outcome_map(self) -> dict[tuple[str, str], SegmentOutcome]:
        return {o.key: o for o in self.outcomes}


@dataclass
class SegmentPreference:
    """市场调研里对某细分偏好结构的结构化描述（先验）。

    数值来自平台市场调研报告（图片型 PDF，人工转写，近似值需回合数据校准）。
    """

    market: str
    segment: str
    price_sensitivity: float = 0.0  # 价格敏感度（越大越敏感；符号见 notes）
    performance_sensitivity: float = 0.0  # 性能敏感度（净推荐值斜率，越大越敏感）
    battery_sensitivity: float = 0.0  # 电池寿命敏感度（购买意愿变化率斜率）
    style_preference: dict[str, float] = field(default_factory=dict)  # 款式 -> 喜好度
    warranty_sensitivity: float = 0.0  # 保修期敏感度
    feature_importance: dict[str, float] = field(default_factory=dict)  # 功能 -> 重要性
    ad_effectiveness: float = 0.0  # 定向广告预算 +10% 带来的销量拉动 %（细分特定）
    channel_reach: dict[str, float] = field(default_factory=dict)  # 渠道 -> 偏好该渠道的客户 %
    size: float = 0.0  # 市场规模相对权重
    growth: float = 0.0
    notes: str = ""


@dataclass
class MarketResearch:
    """市场调研文件的结构化转写（先验来源）。"""

    segments: list[SegmentPreference] = field(default_factory=list)

    def get(self, market: str, segment: str) -> SegmentPreference | None:
        for s in self.segments:
            if s.market == market and s.segment == segment:
                return s
        return None


# ============================================================
# 多产品决策结构（决策指南第 4~7 节）
# ============================================================


@dataclass
class Product:
    """一个产品的配置决策。"""

    name: str = ""
    style: str = ""  # 经典 / 前卫 / 运动
    features: list[str] = field(default_factory=list)  # 最多 5 个附加特征
    thinness: float = 100.0  # 轻薄度技术指数（研发可提升 >100）
    battery: float = 100.0  # 电池寿命技术指数
    markets: list[str] = field(default_factory=list)  # 投放的市场（EU/ASIA/两者/空）
    prices: dict[str, float] = field(default_factory=dict)  # market -> 价格

    def in_market(self, market: str) -> bool:
        return market in self.markets


@dataclass
class TurnDecision:
    """一个回合的完整决策（多产品结构）。"""

    turn: int
    products: list[Product] = field(default_factory=list)
    advertising: dict[str, float] = field(default_factory=dict)  # 键 "市场:细分:产品名" 或 "市场"
    channel_investment: dict[str, float] = field(default_factory=dict)  # 键 "市场:渠道" 或 "市场"
    rd: dict[str, float] = field(default_factory=dict)  # {"thinness": x, "battery": y}
    service: dict[str, float] = field(default_factory=dict)  # 质保/维修质量/维修价格
    payment_terms: float = 0.0
    forecasts: dict[str, float] = field(default_factory=dict)  # 销售预测
    market_research: dict[str, float] = field(default_factory=dict)  # market -> 投入
    notes: str = ""


# ============================================================
# 结果快照（来自结果导出 xls：自身 + 对手全部可见）
# ============================================================


@dataclass
class CompanyResult:
    """一家公司在某回合的结果快照（决策 + 市场/财务结果）。"""

    company: str
    turn: int
    prices: dict[str, float] = field(default_factory=dict)  # "市场:P1" -> 价格
    sales: dict[str, float] = field(default_factory=dict)  # "市场:细分" -> 销量合计
    shares: dict[str, float] = field(default_factory=dict)  # "市场:细分" -> 份额 %
    channel_sales: dict[str, float] = field(default_factory=dict)  # "市场:渠道" -> 销量
    advertising: dict[str, float] = field(default_factory=dict)  # "市场" -> 广告费
    channel_investment: dict[str, float] = field(default_factory=dict)  # "市场" -> 渠道投资
    rd_investment: float = 0.0
    market_research: float = 0.0
    product_attributes: dict[str, dict[str, float]] = field(default_factory=dict)  # "市场:P1" -> 属性
    product_styles: dict[str, str] = field(default_factory=dict)  # "市场:P1" -> 款式
    revenue: float = 0.0
    profit: float = 0.0
    stock_price: float | None = None
    cash: float = 0.0
    extra: dict[str, float] = field(default_factory=dict)


@dataclass
class MarketResult:
    """一个回合全市场的结果快照（12 家公司）。"""

    turn: int
    companies: list[CompanyResult] = field(default_factory=list)

    def company(self, name: str) -> CompanyResult | None:
        for c in self.companies:
            if c.company == name:
                return c
        return None

    def opponents(self, our_name: str) -> list[CompanyResult]:
        return [c for c in self.companies if c.company != our_name]
