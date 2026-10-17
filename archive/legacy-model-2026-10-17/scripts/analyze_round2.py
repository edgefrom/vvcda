"""练习回合 2 决策分析：用 23 份真实结果 xls 拟合弹性 + 定位本队 + 盈利画像。

运行：python scripts/analyze_round2.py
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cda.analysis import load_all_markets, fit_segment_elasticities, benchmark_profitable, profitable_check  # noqa: E402
from cda.adapters.xls_source import parse_results  # noqa: E402

PATTERN = str(ROOT / "data" / "raw" / "results" / "*.xls")

print("== 0. 文件清单 ==")
files = sorted(glob.glob(PATTERN))
for f in files:
    print("  ", Path(f).name)

print("\n== 1. 各赛区公司名（找维维一笑队） ==")
for f in files:
    try:
        m = parse_results(f)
        names = [c.company for c in m.companies]
        hit = [n for n in names if "维维" in n or "一笑" in n]
        print(f"  {Path(f).name}: {len(names)} 家 {names}")
        if hit:
            print(f"    >>> 命中本队: {hit}")
    except Exception as e:
        print(f"  {Path(f).name}: 解析失败 {e}")

print("\n== 2. 分细分弹性（EU 市场，跨 23 赛区池化） ==")
markets = load_all_markets(PATTERN)
print(f"  成功加载 {len(markets)} 个赛区")
for market in ("EU", "ASIA"):
    el = fit_segment_elasticities(markets, market=market)
    print(f"\n  [{market}]")
    print(f"  {'细分':<10} {'价格弹性':>8} {'广告弹性':>8} {'渠道弹性':>8} {'n':>5}")
    for seg, v in el.items():
        print(f"  {seg:<10} {v['rel_price']:>8.3f} {v['rel_ad']:>8.3f} {v['rel_channel']:>8.3f} {v['n']:>5}")

print("\n== 3. 盈利公司画像（EU） ==")
for market in ("EU", "ASIA"):
    b = benchmark_profitable(markets, market=market)
    print(f"  [{market}] {b}")
