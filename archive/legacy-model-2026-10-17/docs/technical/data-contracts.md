# 数据契约（Data Contracts）

本文件精确描述统一数据结构与配置文件的字段含义。改动接口或字段时必须同步更新本文件。

## 核心对象（`src/cda/schemas.py`）

### `DecisionField` — 单个决策字段元信息
| 字段 | 类型 | 含义 |
|---|---|---|
| `name` | str | 字段名（真实平台字段名，由 config 驱动） |
| `unit` | str | 单位（如 EUR、件、千元） |
| `kind` | str | `continuous` / `integer` / `categorical` |
| `lower` / `upper` | float\|None | 取值范围；None=待验证 |
| `default` | float\|None | 默认值 |
| `applies_to` | tuple[str] | 作用于哪些市场；空=全局 |

### `DecisionSchema` — 决策表单结构
- `fields: dict[str, DecisionField]`
- `markets` / `segments`：默认 `("EU","ASIA")` × `("consumer","premium","business","premium_business")`

### `DecisionVector` — 一个回合的决策
- `turn: int`，`values: dict[str, float]`（字段名→数值），`notes: str`

### `SegmentOutcome` — 单个细分结算结果
- `market`、`segment`、`our_sales`（我方销量）、`market_sales`（细分总销量）、`our_share`（[0,1]）

### `Financials` — 财务结果
- `revenue`、`cost`、`profit`、`cash`、`inventory`
- `extra: dict[str, float]` — 未知字段兜底，保证可迁移

### `TurnRecord` — 一回合完整记录
- `turn`、`decision`、`outcomes: list[SegmentOutcome]`、`financials: Financials|None`、`stock_price: float|None`、`extra`

### `SegmentPreference` / `MarketResearch` — 市场调研先验
- `SegmentPreference`：`market`、`segment`、`price_sensitivity`（越大越敏感）、`feature_weights`（功能维度权重）、`ad_sensitivity`、`channel_reach`（渠道可达性）、`size`（规模相对权重）、`growth`、`notes`
- `MarketResearch.segments: list[SegmentPreference]`

## 配置文件

### `config/decision_schema.yaml`
决策表单的字段定义。**这是先验模板**，登录平台后按真实表单逐字段抄录替换。
`lower/upper/default` 填 `null` 表示待验证。

### `config/market_research.yaml`
市场调研文件的结构化转写（**先验来源**）。登录平台下载市场调研文件后逐细分填写。
`null` 表示待填写。`feature_weights` 与 `channel_reach` 是字典（功能/渠道名→权重）。

## 回合记录 JSON 示例（`data/turns/turn_01.json`）

```json
{
  "turn": 1,
  "decision": {"turn": 1, "values": {"price_EU": 399.0, "advertising_EU": 100.0}, "notes": "练习回合：价格档位对照"},
  "outcomes": [
    {"market": "EU", "segment": "consumer", "our_sales": 1200.0, "market_sales": 10000.0, "our_share": 0.12}
  ],
  "financials": {"revenue": 478800.0, "cost": 350000.0, "profit": 128800.0, "cash": 800000.0, "inventory": 0.0, "extra": {}},
  "stock_price": 12.5,
  "extra": {}
}
```

## 约定

- 份额 `our_share` 取 (0,1) 开区间内的值才能参与 logit 需求估计（0 或 1 会被跳过）。
- 未知字段一律进 `extra`，不扩展核心结构。
- **市场规模尺度必须与价格/成本同量纲**：`SegmentPreference.size`（市场调研文件）是
  `make_scenarios` 的 `market_sizes` 来源。若 size 与价格、单位成本不在同一尺度，
  财务仿真的收入与成本会失配，导致优化器给出「产量最小化」等伪最优。未填写 size 时
  回退 1.0，但需尽快用调研文件补全。
- 广告/研发/渠道等营销投入存在边际收益递减：优化时对这些字段用 `transforms={"...":"log"}`
  （对数变换），否则线性模型会在优化时退化到「要么最大、要么最小」的角落解。
