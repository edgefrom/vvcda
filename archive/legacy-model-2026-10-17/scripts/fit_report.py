"""打印完整回归结果：logit(份额) = 截距 + β价·相对价格 + β广·相对广告 + β渠·相对渠道。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cda.adapters.xls_source import parse_results  # noqa: E402
from cda.schemas import SEGMENTS_DEFAULT  # noqa: E402
from cda.analysis import load_all_markets  # noqa: E402

SEGMENTS = list(SEGMENTS_DEFAULT)
SEG_LABELS = {"consumer": "普通消费者", "premium": "高端消费者", "business": "企业用户", "premium_business": "高端企业用户"}


def _logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return float(np.log(p / (1 - p)))


def fit_report(markets, market):
    print(f"\n[{market}]  公式: logit(份额) = β0 + βp·(价格/市场均价) + βa·(广告/市场均值) + βc·(渠道/市场均值)")
    print(f"{'细分':<8}{'β0(截距)':>10}{'βp价格':>9}{'βa广告':>9}{'βc渠道':>9}{'R²':>8}{'n':>6}")
    for seg in SEGMENTS:
        X, y = [], []
        for m in markets:
            prices = []
            for c in m.companies:
                prices += [v for k, v in c.prices.items() if k.startswith(market + ":") and v > 0]
            mp = float(np.mean(prices)) if prices else 1.0
            ads = [c.advertising.get(market, 0.0) for c in m.companies]
            ma = float(np.mean([a for a in ads if a > 0])) if any(a > 0 for a in ads) else 1.0
            chs = [c.channel_investment.get(market, 0.0) for c in m.companies]
            mc = float(np.mean([v for v in chs if v > 0])) if any(v > 0 for v in chs) else 1.0
            for c in m.companies:
                share = c.shares.get(f"{market}:{seg}", 0.0)
                if 0.0 < share < 100.0:
                    ap = float(np.mean([v for k, v in c.prices.items() if k.startswith(market + ":") and v > 0])) or mp
                    X.append([1.0, ap / mp, c.advertising.get(market, 0.0) / ma, c.channel_investment.get(market, 0.0) / mc])
                    y.append(_logit(share / 100.0))
        if len(y) < 10:
            continue
        X, y = np.asarray(X), np.asarray(y)
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        yhat = X @ coef
        r2 = 1 - float(np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2))
        print(f"{SEG_LABELS[seg]:<8}{coef[0]:>10.3f}{coef[1]:>9.3f}{coef[2]:>9.3f}{coef[3]:>9.3f}{r2:>8.3f}{len(y):>6}")


if __name__ == "__main__":
    markets = load_all_markets(str(ROOT / "data" / "raw" / "results" / "*.xls"))
    fit_report(markets, "EU")
    fit_report(markets, "ASIA")
