"""深入分析维维一笑队所在赛区（results-pr01 (13).xls）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cda.adapters.xls_source import parse_results  # noqa: E402

SEGMENTS = ["consumer", "premium", "business", "premium_business"]
SEG_LABELS = {"consumer": "普通消费者", "premium": "高端消费者", "business": "企业用户", "premium_business": "高端企业用户"}
CHANNELS = ["品牌专卖店", "家电卖场", "百货商场"]

f = ROOT / "data" / "raw" / "results" / "results-pr01 (13).xls"
m = parse_results(str(f))

print(f"赛区: results-pr01 (13).xls | {len(m.companies)} 家\n")

# 按利润排序输出全表
rows = sorted(m.companies, key=lambda c: c.profit, reverse=True)
print("== 全赛区对比（按利润降序） ==")
print(f"{'公司':<14} {'利润':>10} {'收入':>10} {'股价':>6} {'EU产品':>6} {'AS产品':>6} {'EU广告':>7} {'AS广告':>7} {'研发':>6}")
for c in rows:
    eu_prod = len([k for k in c.prices if k.startswith("EU:")])
    as_prod = len([k for k in c.prices if k.startswith("ASIA:")])
    print(f"{c.company:<14} {c.profit:>10.0f} {c.revenue:>10.0f} {c.stock_price or 0:>6.2f} {eu_prod:>6} {as_prod:>6} {c.advertising.get('EU',0):>7.0f} {c.advertising.get('ASIA',0):>7.0f} {c.rd_investment:>6.0f}")

print("\n== 维维一笑队 详情 ==")
us = m.company("维维一笑队")
if us:
    for k in sorted(us.prices):
        print(f"  price[{k}] = {us.prices[k]}")
    print("  EU 份额:", {f"{SEG_LABELS[s]}:{us.shares.get(f'EU:{s}',0):.1f}%" for s in SEGMENTS})
    print("  ASIA 份额:", {f"{SEG_LABELS[s]}:{us.shares.get(f'ASIA:{s}',0):.1f}%" for s in SEGMENTS})
    print("  EU 销量:", {f"{SEG_LABELS[s]}:{us.sales.get(f'EU:{s}',0):.0f}" for s in SEGMENTS})
    print("  ASIA 销量:", {f"{SEG_LABELS[s]}:{us.sales.get(f'ASIA:{s}',0):.0f}" for s in SEGMENTS})
    print("  EU 渠道销量:", {ch: f"{us.channel_sales.get(f'EU:{ch}',0):.0f}" for ch in CHANNELS})
    print("  ASIA 渠道销量:", {ch: f"{us.channel_sales.get(f'ASIA:{ch}',0):.0f}" for ch in CHANNELS})
    print("  广告:", us.advertising, "| 渠道投资:", us.channel_investment)
    print("  研发:", us.rd_investment, "| 市场调研:", us.market_research)
    print("  产品属性:", us.product_attributes)
    print("  款式:", us.product_styles)
    print(f"  收入 {us.revenue:.0f} | 利润 {us.profit:.0f} | 股价 {us.stock_price} | 现金 {us.cash:.0f}")

# 市场总销量（EU/ASIA 各细分合计）
print("\n== 本赛区市场总销量（各细分所有公司销量合计） ==")
for mk in ("EU", "ASIA"):
    tot = {s: sum(c.sales.get(f"{mk}:{s}", 0.0) for c in m.companies) for s in SEGMENTS}
    grand = sum(tot.values())
    print(f"  {mk}: " + " ".join(f"{SEG_LABELS[s]}={tot[s]:.0f}" for s in SEGMENTS) + f" | 合计={grand:.0f}")

# 维维一笑各细分总销量
print("\n== 维维一笑队 各细分总销量（千件） ==")
for mk in ("EU", "ASIA"):
    tot = sum(us.sales.get(f"{mk}:{s}", 0.0) for s in SEGMENTS)
    print(f"  {mk} 合计 = {tot:.1f}")

# 对手平均价格（供相对价格参考）
print("\n== 各市场对手平均价（本赛区） ==")
for mk in ("EU", "ASIA"):
    ps = []
    for c in m.companies:
        for k, v in c.prices.items():
            if k.startswith(mk + ":") and v > 0:
                ps.append(v)
    if ps:
        import statistics
        print(f"  {mk}: 均价 {statistics.mean(ps):.0f} | 中位 {statistics.median(ps):.0f} | min {min(ps):.0f} | max {max(ps):.0f} | n={len(ps)}")
