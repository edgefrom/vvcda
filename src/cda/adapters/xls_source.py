"""结果导出 xls 解析器：把 CESIM 结果导出（宽表）解析为 MarketResult。

结果导出是宽表：73 列 = 1 个标签列 + 12 家公司 × 6 个产品列（P1~P6）。
本解析器把每家公司（含对手）的决策与结果提取为 CompanyResult，
是「对手决策完全可见」这一事实的落地入口。

运行：python scripts/parse_results.py  或  from cda.adapters.xls_source import parse_results
"""
from __future__ import annotations

import pandas as pd

from ..schemas import CompanyResult, MarketResult

SEGMENTS = ["consumer", "premium", "business", "premium_business"]
SEGMENT_LABELS = ["普通消费者", "高端消费者", "企业用户", "高端企业用户"]
CHANNELS = ["品牌专卖店", "家电卖场", "百货商场"]
FEATURES = ["高像素", "额外存储", "高级屏幕", "导航功能", "安全功能"]

# 行号（0 基，header=None）。对应 results-ir00.xls 的指标行。
_ROWS = {
    "eu_price": 3, "eu_sales": 6, "eu_channel": 14, "eu_share": 19,
    "eu_ad": 25, "eu_channel_inv": 26,
    "eu_thinness": 29, "eu_battery": 30, "eu_features": 32, "eu_style": 37,
    "asia_price": 42, "asia_sales": 45, "asia_channel": 53, "asia_share": 58,
    "asia_ad": 64, "asia_channel_inv": 65,
    "asia_thinness": 68, "asia_battery": 69, "asia_features": 71, "asia_style": 76,
    "revenue": 208, "profit": 238, "stock_price": 274, "cash": 249,
    "rd": 226, "market_research": 227,
}


def _num(df: pd.DataFrame, row: int, col: int) -> float:
    v = df.iloc[row, col]
    try:
        return 0.0 if pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return 0.0


def _sum_block(df: pd.DataFrame, row: int, base: int, width: int = 6) -> float:
    vals = [df.iloc[row, base + j] for j in range(width)]
    nums = []
    for v in vals:
        try:
            if not pd.isna(v):
                nums.append(float(v))
        except (TypeError, ValueError):
            continue
    return sum(nums)


def _per_product_map(df: pd.DataFrame, row: int, base: int, market: str, width: int = 6) -> dict[str, float]:
    out: dict[str, float] = {}
    for j in range(width):
        v = _num(df, row, base + j)
        if v != 0.0 or not pd.isna(df.iloc[row, base + j]):
            out[f"{market}:P{j + 1}"] = v
    return out


def _company_columns(df: pd.DataFrame) -> list[tuple[str, int]]:
    """返回 [(公司名, 列基准)]。公司名在行 1，每家占 6 列。"""
    out: list[tuple[str, int]] = []
    row = df.iloc[1]
    for col in range(1, df.shape[1]):
        val = str(row[col]).strip().replace(" ", "")
        if val and val != "nan" and val.startswith("公司"):
            out.append((val, col))
    return out


def _product_exists(df: pd.DataFrame, base: int, j: int) -> bool:
    col = base + j
    for r in (_ROWS["eu_price"], _ROWS["asia_price"]):
        try:
            if not pd.isna(df.iloc[r, col]):
                return True
        except IndexError:
            pass
    return False


def _extract_product_attributes(
    df: pd.DataFrame, base: int, market: str, price_row: int, thin_row: int, batt_row: int, feat_row: int, style_row: int
) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    attrs: dict[str, dict[str, float]] = {}
    styles: dict[str, str] = {}
    for j in range(6):
        if not _product_exists(df, base, j):
            continue
        key = f"{market}:P{j + 1}"
        attr = {"thinness": _num(df, thin_row, base + j), "battery": _num(df, batt_row, base + j)}
        for k, feat in enumerate(FEATURES):
            attr[feat] = _num(df, feat_row + k, base + j)
        attrs[key] = attr
        style_val = str(df.iloc[style_row, base + j]).strip()
        if style_val and style_val != "nan":
            styles[key] = style_val
    return attrs, styles


def parse_results(path: str, turn: int = 0) -> MarketResult:
    """解析结果导出 xls，返回全市场快照。"""
    df = pd.read_excel(path, sheet_name=0, header=None)
    # 布局说明：市场区（产品/定价/销量/份额/广告/渠道）= 每公司 6 列（6 产品）；
    # 财务区（研发/市场调研/利润/股价/现金）= 每公司 1 列，12 家连续排列。
    companies: list[CompanyResult] = []
    company_columns = _company_columns(df)
    for idx, (name, base) in enumerate(company_columns):
        fin_col = 1 + idx  # 财务区：每公司 1 列
        c = CompanyResult(company=name, turn=turn)
        c.prices = _per_product_map(df, _ROWS["eu_price"], base, "EU")
        c.prices.update(_per_product_map(df, _ROWS["asia_price"], base, "ASIA"))
        for i, seg in enumerate(SEGMENTS):
            c.sales[f"EU:{seg}"] = _sum_block(df, _ROWS["eu_sales"] + i, base)
            c.sales[f"ASIA:{seg}"] = _sum_block(df, _ROWS["asia_sales"] + i, base)
            c.shares[f"EU:{seg}"] = _sum_block(df, _ROWS["eu_share"] + i, base)
            c.shares[f"ASIA:{seg}"] = _sum_block(df, _ROWS["asia_share"] + i, base)
        for i, ch in enumerate(CHANNELS):
            c.channel_sales[f"EU:{ch}"] = _sum_block(df, _ROWS["eu_channel"] + i, base)
            c.channel_sales[f"ASIA:{ch}"] = _sum_block(df, _ROWS["asia_channel"] + i, base)
        c.advertising["EU"] = _sum_block(df, _ROWS["eu_ad"], base)
        c.advertising["ASIA"] = _sum_block(df, _ROWS["asia_ad"], base)
        c.channel_investment["EU"] = _sum_block(df, _ROWS["eu_channel_inv"], base)
        c.channel_investment["ASIA"] = _sum_block(df, _ROWS["asia_channel_inv"], base)
        c.rd_investment = _num(df, _ROWS["rd"], fin_col)
        c.market_research = _num(df, _ROWS["market_research"], fin_col)
        eu_attrs, eu_styles = _extract_product_attributes(
            df, base, "EU", _ROWS["eu_price"], _ROWS["eu_thinness"], _ROWS["eu_battery"], _ROWS["eu_features"], _ROWS["eu_style"]
        )
        asia_attrs, asia_styles = _extract_product_attributes(
            df, base, "ASIA", _ROWS["asia_price"], _ROWS["asia_thinness"], _ROWS["asia_battery"], _ROWS["asia_features"], _ROWS["asia_style"]
        )
        c.product_attributes = {**eu_attrs, **asia_attrs}
        c.product_styles = {**eu_styles, **asia_styles}
        c.revenue = _num(df, _ROWS["revenue"], fin_col)
        c.profit = _num(df, _ROWS["profit"], fin_col)
        sp = _num(df, _ROWS["stock_price"], fin_col)
        c.stock_price = sp if sp else None
        c.cash = _num(df, _ROWS["cash"], fin_col)
        companies.append(c)
    return MarketResult(turn=turn, companies=companies)


class XlsResultsSource:
    """结果导出 xls 数据源。"""

    def __init__(self, path: str, turn: int = 0) -> None:
        self.path = path
        self.turn = turn

    def load(self) -> MarketResult:
        return parse_results(self.path, self.turn)
