"""建议对象与 Markdown 渲染。

设计目标（机制说明书 P7）：输出「推荐值 + 依据 + 置信度 + 备选 + 风险」，
让 4 名队员能在几分钟内理解、审核、否决。精确但没人看得懂的数值没有价值。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..schemas import DecisionVector


@dataclass
class Alternative:
    decision: DecisionVector
    rationale: str = ""


@dataclass
class Recommendation:
    turn: int
    decision: DecisionVector
    rationale: str = ""
    confidence: str = "low"  # low | medium | high
    alternatives: list[Alternative] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines: list[str] = []
        lines.append(f"## 第 {self.turn} 回合 · 建议")
        lines.append("")
        lines.append(f"**置信度**：{self.confidence}")
        lines.append("")
        lines.append("### 推荐决策")
        lines.append("")
        lines.append("| 字段 | 值 |")
        lines.append("|---|---|")
        for k, v in sorted(self.decision.values.items()):
            lines.append(f"| {k} | {v:g} |")
        lines.append("")
        lines.append(f"**一句话理由**：{self.rationale}")
        lines.append("")
        if self.alternatives:
            lines.append("### 备选方案")
            lines.append("")
            for i, alt in enumerate(self.alternatives, 1):
                vals = "，".join(f"{k}={v:g}" for k, v in sorted(alt.decision.values.items()))
                lines.append(f"{i}. {vals} — {alt.rationale}")
            lines.append("")
        if self.risks:
            lines.append("### 风险提示")
            lines.append("")
            for r in self.risks:
                lines.append(f"- {r}")
            lines.append("")
        lines.append("> ⚠️ 本建议由决策支持工具生成，仅供团队讨论参考。")
        lines.append("> 最终经营决策由团队理解、讨论并人工提交。")
        return "\n".join(lines)
