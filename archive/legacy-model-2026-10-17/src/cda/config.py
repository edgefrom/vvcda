"""配置加载：读取 config/*.yaml 为统一结构。"""
from __future__ import annotations

from typing import Any

import yaml

from .schemas import (
    DecisionField,
    DecisionSchema,
    MarketResearch,
    SegmentPreference,
    SEGMENTS_DEFAULT,
    MARKETS_DEFAULT,
)


def load_decision_schema(path: str) -> DecisionSchema:
    with open(path, encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}
    fields: dict[str, DecisionField] = {}
    for name, f in (data.get("fields") or {}).items():
        fields[name] = DecisionField(
            name=str(f.get("name", name)),
            unit=str(f.get("unit", "")),
            kind=str(f.get("kind", "continuous")),
            lower=f.get("lower"),
            upper=f.get("upper"),
            default=f.get("default"),
            applies_to=tuple(f.get("applies_to") or ()),
        )
    return DecisionSchema(
        fields=fields,
        markets=tuple(data.get("markets") or MARKETS_DEFAULT),
        segments=tuple(data.get("segments") or SEGMENTS_DEFAULT),
    )


def load_market_research(path: str) -> MarketResearch:
    with open(path, encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}
    segments: list[SegmentPreference] = []
    for item in data.get("segments") or []:
        segments.append(
            SegmentPreference(
                market=str(item.get("market", "")),
                segment=str(item.get("segment", "")),
                price_sensitivity=_opt_float(item.get("price_sensitivity")),
                performance_sensitivity=_opt_float(item.get("performance_sensitivity")),
                battery_sensitivity=_opt_float(item.get("battery_sensitivity")),
                style_preference={str(k): float(v) for k, v in (item.get("style_preference") or {}).items()},
                warranty_sensitivity=_opt_float(item.get("warranty_sensitivity")),
                feature_importance={str(k): float(v) for k, v in (item.get("feature_importance") or {}).items()},
                ad_effectiveness=_opt_float(item.get("ad_effectiveness")),
                channel_reach={str(k): float(v) for k, v in (item.get("channel_reach") or {}).items()},
                size=_opt_float(item.get("size")),
                growth=_opt_float(item.get("growth")),
                notes=str(item.get("notes", "")),
            )
        )
    return MarketResearch(segments=segments)


def _opt_float(value: Any) -> float:
    return 0.0 if value is None else float(value)
